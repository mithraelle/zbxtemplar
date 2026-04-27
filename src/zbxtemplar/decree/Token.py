import time

from zbxtemplar.dicts.Schema import SchemaField, FieldPolicy
from zbxtemplar.decree.DecreeEntity import DecreeEntity


class Token(DecreeEntity):
    """API token provisioning settings for a managed user."""

    STDOUT = "STDOUT"
    EXPIRES_NEVER = "NEVER"

    _SCHEMA = [
        SchemaField("name", optional=False, str_type="str", description="API token name."),
        SchemaField("store_at", optional=False, str_type="str | STDOUT", description="Output sink for the generated token secret: a file path or STDOUT.", policy=FieldPolicy.IGNORE),
        SchemaField("expires_at", str_type="int | NEVER", description="Token expiration as a future Unix timestamp, or NEVER for a non-expiring token."),
    ]

    name: str
    store_at: str
    expires_at: int | str | None

    def __init__(self, name: str, store_at: str, expires_at: int | str | None = None):
        self._wire_up(name=name, store_at=store_at, expires_at=expires_at)
        self._check()

    def _wire_up(self, **kwargs) -> None:
        super()._wire_up(**kwargs)
        self.expires_at = self._normalize_expires_at(self.expires_at)

    def _check(self) -> None:
        if not self.name:
            raise ValueError("token.name must be a non-empty string")
        if not self.store_at:
            raise ValueError("token.store_at must be a file path or STDOUT")

    @classmethod
    def _normalize_expires_at(cls, expires_at: int | str | None) -> int | str | None:
        if expires_at is None or expires_at == "":
            return None
        if expires_at == cls.EXPIRES_NEVER:
            return cls.EXPIRES_NEVER
        if isinstance(expires_at, str) and expires_at.isdigit():
            expires_at = int(expires_at)
        if isinstance(expires_at, int) and not isinstance(expires_at, bool):
            return expires_at
        raise ValueError("token.expires_at must be a Unix timestamp or NEVER")

    def assert_expires_in_future(self) -> None:
        if isinstance(self.expires_at, int) and self.expires_at <= int(time.time()):
            raise ValueError("token.expires_at is in the past")