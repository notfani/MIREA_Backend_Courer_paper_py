from cryptography.fernet import Fernet
import os

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY environment variable is not set")

try:
    cipher_suite = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
except Exception as e:
    raise ValueError(f"ENCRYPTION_KEY must be a valid Fernet key (44 chars base64): {e}")


def encrypt_message(message: str) -> str:
    encrypted_bytes = cipher_suite.encrypt(message.encode())
    return encrypted_bytes.decode()

def decrypt_message(encrypted_message: str) -> str:
    decrypted_bytes = cipher_suite.decrypt(encrypted_message.encode())
    return decrypted_bytes.decode()