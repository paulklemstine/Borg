import os
import json
from getpass import getpass
from web3 import Web3
from eth_account import Account
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# --- Configuration ---
INFURA_URL = "https://mainnet.gateway.tenderly.co"
KEY_FILE_DIR = os.path.expanduser("~/.eth_wallets")

# --- Initialize Web3 ---
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """Derives a key from a password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_private_key(private_key: str, password: str) -> dict:
    """Encrypts a private key with a password."""
    salt = os.urandom(16)
    key = generate_key_from_password(password, salt)
    fernet = Fernet(key)
    encrypted_pk = fernet.encrypt(private_key.encode())
    return {
        "encrypted_pk": encrypted_pk.decode(),
        "salt": salt.hex()
    }

def decrypt_private_key(encrypted_data: dict, password: str) -> str:
    """Decrypts a private key with a password."""
    salt = bytes.fromhex(encrypted_data["salt"])
    key = generate_key_from_password(password, salt)
    fernet = Fernet(key)
    decrypted_pk = fernet.decrypt(encrypted_data["encrypted_pk"].encode())
    return decrypted_pk.decode()

def create_new_wallet():
    """Generates a new Ethereum wallet and saves the encrypted private key."""
    account = Account.create()
    private_key = account.key.hex()
    address = account.address

    print(f"Generated new wallet:")
    print(f"  Address: {address}")
    print("Please set a strong password to encrypt your private key.")

    password = getpass("Enter a password: ")
    password_confirm = getpass("Confirm password: ")

    if password != password_confirm:
        print("Passwords do not match. Aborting.")
        return

    encrypted_data = encrypt_private_key(private_key, password)

    if not os.path.exists(KEY_FILE_DIR):
        os.makedirs(KEY_FILE_DIR)

    key_file_path = os.path.join(KEY_FILE_DIR, f"{address}.json")
    with open(key_file_path, "w") as f:
        json.dump(encrypted_data, f, indent=4)

    print(f"Wallet created and private key encrypted.")
    print(f"Key file saved at: {key_file_path}")
    print("IMPORTANT: Store your password and key file securely. Losing them will result in permanent loss of funds.")

def get_eth_balance(address: str):
    """Fetches the ETH balance for a given address."""
    if not web3.is_address(address):
        print(f"Error: '{address}' is not a valid Ethereum address.")
        return

    try:
        balance_wei = web3.eth.get_balance(address)
        balance_eth = web3.from_wei(balance_wei, 'ether')
        print(f"Balance for {address}: {balance_eth} ETH")
        return balance_eth
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return None

def main():
    """Main function to run the CLI."""
    import argparse
    parser = argparse.ArgumentParser(description="A simple, non-custodial Ethereum wallet management tool.")

    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    # Command: create
    parser_create = subparsers.add_parser('create', help='Generate a new Ethereum wallet.')

    # Command: balance
    parser_balance = subparsers.add_parser('balance', help='Fetch the ETH balance for an address.')
    parser_balance.add_argument('address', type=str, help='The Ethereum address to check.')

    # Command: creator-balance
    parser_creator = subparsers.add_parser('creator-balance', help="Fetch the creator's ETH balance.")

    args = parser.parse_args()

    if args.command == 'create':
        create_new_wallet()
    elif args.command == 'balance':
        get_eth_balance(args.address)
    elif args.command == 'creator-balance':
        creator_address = "0x419CA6f5b6F795604938054c951c94d8629AE5Ed"
        print("Fetching balance for the creator's address...")
        get_eth_balance(creator_address)

if __name__ == '__main__':
    main()