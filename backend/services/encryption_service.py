"""
Encryption Service for MT5_UI

Provides encryption/decryption for sensitive data like passwords and API keys.
Uses Fernet symmetric encryption (AES 128-bit).
"""

from cryptography.fernet import Fernet
import os
import base64
from pathlib import Path
from typing import Optional


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self, key_file: Optional[str] = None):
        """
        Initialize encryption service.

        Args:
            key_file: Path to encryption key file. If None, uses default location.
        """
        if key_file is None:
            key_file = "config/.encryption_key"

        self.key_file = Path(key_file)
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        """
        Load encryption key from file or generate new one.

        Returns:
            Encryption key bytes
        """
        # Ensure config directory exists
        self.key_file.parent.mkdir(parents=True, exist_ok=True)

        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, "rb") as f:
                key = f.read()
            return key
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)

            # Set restrictive permissions (owner read/write only)
            try:
                os.chmod(self.key_file, 0o600)
            except Exception:
                # Windows doesn't support chmod the same way
                pass

            return key

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""

        encrypted = self.cipher.encrypt(plaintext.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""

        try:
            encrypted = base64.b64decode(ciphertext.encode("utf-8"))
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}")

    def encrypt_dict(self, data: dict, keys_to_encrypt: list[str]) -> dict:
        """
        Encrypt specific keys in a dictionary.

        Args:
            data: Dictionary containing data
            keys_to_encrypt: List of keys to encrypt

        Returns:
            Dictionary with specified keys encrypted
        """
        encrypted_data = data.copy()
        for key in keys_to_encrypt:
            if key in encrypted_data and encrypted_data[key]:
                encrypted_data[key] = self.encrypt(str(encrypted_data[key]))
        return encrypted_data

    def decrypt_dict(self, data: dict, keys_to_decrypt: list[str]) -> dict:
        """
        Decrypt specific keys in a dictionary.

        Args:
            data: Dictionary containing encrypted data
            keys_to_decrypt: List of keys to decrypt

        Returns:
            Dictionary with specified keys decrypted
        """
        decrypted_data = data.copy()
        for key in keys_to_decrypt:
            if key in decrypted_data and decrypted_data[key]:
                try:
                    decrypted_data[key] = self.decrypt(decrypted_data[key])
                except Exception:
                    # If decryption fails, assume it's already plaintext
                    pass
        return decrypted_data

    def mask_sensitive_data(self, data: str, visible_chars: int = 4) -> str:
        """
        Mask sensitive data, showing only last N characters.

        Args:
            data: Sensitive data to mask
            visible_chars: Number of characters to show at end

        Returns:
            Masked string (e.g., "****5678")
        """
        if not data or len(data) <= visible_chars:
            return "****"

        return "*" * (len(data) - visible_chars) + data[-visible_chars:]


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get global encryption service instance (singleton).

    Returns:
        EncryptionService instance
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
