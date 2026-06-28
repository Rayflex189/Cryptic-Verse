import base64
import hashlib
from django.conf import settings
from cryptography.fernet import Fernet

_fernet = None

def get_fernet():
    global _fernet
    if _fernet is None:
        # Generate a 32-byte key from django settings SECRET_KEY
        key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key_b64 = base64.urlsafe_b64encode(key)
        _fernet = Fernet(key_b64)
    return _fernet

def encrypt_value(value: str) -> str:
    if not value:
        return ""
    f = get_fernet()
    return f.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value: str) -> str:
    if not encrypted_value:
        return ""
    f = get_fernet()
    try:
        return f.decrypt(encrypted_value.encode()).decode()
    except Exception:
        return "[Decryption Error]"
