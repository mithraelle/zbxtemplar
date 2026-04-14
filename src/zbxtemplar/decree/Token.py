from enum import Enum

from zbxtemplar.dicts.DictEntity import DictEntity, SchemaField
from zbxtemplar.decree.DecreeEntity import DecreeEntity


class TokenOutput(Enum):
    """Sentinel for stdout output."""
    STDOUT = "STDOUT"


class TokenExpiry(Enum):
    """Sentinel for non-expiring tokens."""
    NEVER = "NEVER"


class Token(DecreeEntity, DictEntity):
    """API token provisioning settings for a managed user."""

    STDOUT = TokenOutput.STDOUT
    NEVER = TokenExpiry.NEVER

    _SCHEMA = [
        SchemaField("name", optional=False, description="API token name."),
        SchemaField("store_at", optional=False, description="Output sink for the generated token secret: a file path or STDOUT."),
        SchemaField("expires_at", str_type="int | NEVER", description="Token expiration as a future Unix timestamp, or NEVER for a non-expiring token."),
    ]

    def __init__(self, name: str, store_at, expires_at=None):
        self.name = self._normalize_name(name)
        self.store_at = self._normalize_store_at(store_at)
        self.expires_at = self._normalize_expires_at(expires_at)

    @staticmethod
    def _normalize_name(name):
        if not isinstance(name, str) or not name:
            raise ValueError("token.name must be a non-empty string")
        return name

    @classmethod
    def _normalize_store_at(cls, store_at):
        if isinstance(store_at, TokenOutput):
            return store_at
        if isinstance(store_at, str):
            if store_at == "STDOUT":
                return TokenOutput.STDOUT
            if store_at:
                return store_at
        raise ValueError("token.store_at must be a file path or STDOUT")

    @classmethod
    def _normalize_expires_at(cls, expires_at):
        if expires_at is None or expires_at == "":
            return None
        if isinstance(expires_at, TokenExpiry):
            return expires_at
        if isinstance(expires_at, str):
            if expires_at == "NEVER":
                return TokenExpiry.NEVER
            if expires_at.isdigit():
                expires_at = int(expires_at)
        if isinstance(expires_at, int) and not isinstance(expires_at, bool):
            import time
            if expires_at <= int(time.time()):
                raise ValueError("token.expires_at is in the past")
            return expires_at
        raise ValueError("token.expires_at must be a Unix timestamp or NEVER")

    @classmethod
    def from_dict(cls, data: dict):
        if not isinstance(data, dict):
            raise ValueError("token must be a mapping")
        cls.validate(data)
        return cls(
            name=data["name"],
            store_at=data["store_at"],
            expires_at=data.get("expires_at"),
        )
