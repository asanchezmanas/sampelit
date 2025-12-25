# engine/state/encryption.py

"""
State Encryption Module

⚠️  CRITICAL SECURITY MODULE

This module handles encryption/decryption of algorithm internal state
before storing in database.

We NEVER store raw algorithm parameters (alpha, beta, epsilon, etc.)
in plaintext in the database.
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import os
import base64
from typing import Dict, Any, List
from config.settings import settings

class StateEncryption:
    """
    Handles encryption of algorithm state
    
    This ensures that even if someone gets DB access,
    they can't see our Thompson Sampling parameters, etc.
    """
    
    def __init__(self):
        # Key derivada de secret (no hardcoded)
        self.encryption_key = self._derive_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _derive_key(self) -> bytes:
        """
        Derive encryption key from environment secret
        
        This way key is never in code or DB
        """
        secret = settings.ALGORITHM_STATE_SECRET
        if not secret:
            raise ValueError(
                "ALGORITHM_STATE_SECRET not set in settings or environment. "
                "This is CRITICAL for protecting algorithm internals."
            )
        
        # Derive key using PBKDF2
        salt = b'samplit_algorithm_state_v1'  # Fixed salt OK here
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return key
    
    def encrypt_state(self, state_data: Dict[str, Any]) -> bytes:
        """
        Encrypt algorithm state before storing in DB
        
        Args:
            state_data: Dict with algorithm parameters
                       Example: {'alpha': 5.0, 'beta': 3.0, ...}
        
        Returns:
            Encrypted binary data for DB storage
        """
        
        # Serialize to JSON
        json_data = json.dumps(state_data, sort_keys=True)
        
        # Encrypt
        encrypted = self.fernet.encrypt(json_data.encode())
        
        return encrypted
    
    def decrypt_state(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Decrypt algorithm state from DB
        
        Args:
            encrypted_data: Binary data from DB
        
        Returns:
            Decrypted state dictionary
        """
        
        # Decrypt
        decrypted = self.fernet.decrypt(encrypted_data)
        
        # Parse JSON
        state_data = json.loads(decrypted.decode())
        
        return state_data
    
    def encrypt_path_data(self, path: List[str]) -> bytes:
        """
        Encrypt funnel path data
        
        We don't want variant IDs visible in plaintext
        """
        path_json = json.dumps(path)
        return self.fernet.encrypt(path_json.encode())
    
    def decrypt_path_data(self, encrypted_path: bytes) -> List[str]:
        """Decrypt funnel path"""
        decrypted = self.fernet.decrypt(encrypted_path)
        return json.loads(decrypted.decode())

# Singleton instance
_encryptor = None

def get_encryptor() -> StateEncryption:
    """Get singleton encryptor instance"""
    global _encryptor
    if _encryptor is None:
        _encryptor = StateEncryption()
    return _encryptor
