from cryptography.fernet import Fernet, MultiFernet
from os import environ
from typing import List, Optional


class FernetWrapper:
    ENV_ENCRYPTION_KEYS = "SNOWFLAKE_CONFIG_FERNET_KEYS"

    def __init__(self, explicit_encryption_keys: Optional[str] = None):
        self.key_sequence: List[str] = []
        self.multi_fernet: Optional[MultiFernet] = None

        if explicit_encryption_keys:
            self.key_sequence = self._parse_encryption_keys(explicit_encryption_keys)
        elif self.ENV_ENCRYPTION_KEYS in environ:
            self.key_sequence = self._parse_encryption_keys(environ[self.ENV_ENCRYPTION_KEYS])

        if self.key_sequence:
            self.multi_fernet = MultiFernet(Fernet(key) for key in self.key_sequence)

    def generate_key(self):
        return Fernet.generate_key().decode("ascii")

    def encrypt(self, value: str):
        if not self.multi_fernet:
            raise RuntimeError("Cannot encrypt value due to missing Fernet encryption keys")

        return self.multi_fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str):
        if not self.multi_fernet:
            raise RuntimeError("Cannot decrypt value due to missing Fernet encryption keys")

        return self.multi_fernet.decrypt(value.encode("ascii")).decode("utf-8")

    def rotate(self, value: str):
        if not self.multi_fernet:
            raise RuntimeError("Cannot rotate value due to missing Fernet encryption keys")

        return self.multi_fernet.rotate(value.encode("ascii")).decode("ascii")

    def _parse_encryption_keys(self, encryption_keys: str):
        key_sequence = []

        for key in encryption_keys.split(","):
            key = key.strip()

            if not key:
                continue

            key_sequence.append(key)

        return key_sequence
