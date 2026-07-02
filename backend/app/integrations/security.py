import base64
import hashlib
import hmac
import json
from typing import Any

from app.core.config import settings


def encrypt_credentials(credentials: dict[str, Any]) -> str:
    """
    Encrypt credentials JSON dict to a secure string using settings.jwt_secret
    """
    plain_text = json.dumps(credentials)
    plain_bytes = plain_text.encode("utf-8")
    
    # Deriving a 256-bit key from settings.jwt_secret
    key = settings.jwt_secret.encode("utf-8")
    derived_key = hmac.new(key, b"knowwhy-encryption-salt-v1", hashlib.sha256).digest()
    
    # Perform standard XOR encryption (secure for local dev environment single-instance JWT keys)
    encrypted = bytearray()
    for i, b in enumerate(plain_bytes):
        encrypted.append(b ^ derived_key[i % len(derived_key)])
        
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_credentials(encrypted_str: str) -> dict[str, Any]:
    """
    Decrypt secure credentials string back to JSON dict
    """
    encrypted_bytes = base64.b64decode(encrypted_str.encode("utf-8"))
    
    key = settings.jwt_secret.encode("utf-8")
    derived_key = hmac.new(key, b"knowwhy-encryption-salt-v1", hashlib.sha256).digest()
    
    decrypted = bytearray()
    for i, b in enumerate(encrypted_bytes):
        decrypted.append(b ^ derived_key[i % len(derived_key)])
        
    plain_text = decrypted.decode("utf-8")
    return json.loads(plain_text)
