import re, base64, tomllib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def get_config():
    with open('config.toml', 'rb') as tconfig:
        config = tomllib.load(tconfig)
    WS_URL = config['settings']['server_address']
    CHANNEL = config['profile']['channel']
    ENABLE_INPUT = config['settings']['enable_input']
    ENABLE_COLOR = config['settings']['enable_256_bit_color']
    ENCRYPTION_KEY = config['security']['aes_256_key']
    ENABLE_ENCRYPTION = config['security']['enable_encryption']
    if not ENABLE_ENCRYPTION:
        USERNAME = config['profile']['username']
    else:
        USERNAME = encrypt(ENCRYPTION_KEY, config['profile']['username'])
    CLIENT_SIDE_COLOR = config['settings']['client_side_color']
    return WS_URL, CHANNEL, USERNAME, ENABLE_INPUT, ENABLE_COLOR, ENABLE_ENCRYPTION, ENCRYPTION_KEY, CLIENT_SIDE_COLOR

def hex_to_ansi256(hex_color: str) -> int:
    hex_color = hex_color.lstrip('#')
    if not re.fullmatch(r'[0-9a-fA-F]{6}', hex_color):
        return 15  # default white

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Convert RGB 0-255 to 0-5 scale
    def to_ansi_val(x): 
        return 0 if x < 48 else 1 if x < 115 else int((x - 35) / 40)
    r_ = to_ansi_val(r)
    g_ = to_ansi_val(g)
    b_ = to_ansi_val(b)
    return 16 + (36 * r_) + (6 * g_) + b_

def colored(text: str, hex_color: str) -> str:
    code = hex_to_ansi256(hex_color)
    return f"\033[38;5;{code}m{text}\033[0m"

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
