import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import time, os, random

def encrypt(hex_key: str, plaintext: str) -> str:
    key = bytes.fromhex(hex_key)
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad manually to 16 bytes (AES block size)
    padded = plaintext.encode()
    padding_len = 16 - (len(padded) % 16)
    padded += bytes([padding_len]) * padding_len

    ct = encryptor.update(padded) + encryptor.finalize()
    return base64.urlsafe_b64encode(ct).decode().rstrip("=")  # no "/" or "+" or "="

def decrypt(hex_key: str, b64_ciphertext: str) -> str:
    key = bytes.fromhex(hex_key)
    b64_ciphertext += '=' * (-len(b64_ciphertext) % 4)  # fix padding
    ct = base64.urlsafe_b64decode(b64_ciphertext)

    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()

    # Remove PKCS7-style padding
    pad_len = padded[-1]
    return padded[:-pad_len].decode()

def time_ago(past_epoch: int | float, raw_seconds: bool = False) -> str | int:
    now = int(time.time())
    diff = now - int(past_epoch)

    if raw_seconds:
        return diff
    if diff < 60:
        return f"{diff}s ago"
    elif diff < 3600:
        return f"{diff // 60}m ago"
    else:
        return f"{diff // 3600}h ago"

if __name__ == '__main__':
    print(f'keygen: {os.urandom(256 // 8).hex()}\nchannel: {random.randint(1, 100000000000)}')
