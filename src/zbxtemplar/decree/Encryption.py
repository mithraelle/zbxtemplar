import copy
from enum import Enum

from zbxtemplar.dicts.DictEntity import DictEntity, SchemaField


class EncryptionMode(Enum):
    UNENCRYPTED = 1
    PSK = 2
    CERT = 4

    @classmethod
    def from_string(cls, value: str) -> "EncryptionMode":
        value_upper = value.upper()
        if value_upper == "UNENCRYPTED":
            return cls.UNENCRYPTED
        if value_upper == "PSK":
            return cls.PSK
        if value_upper == "CERT":
            return cls.CERT
        raise ValueError(f"Unknown EncryptionMode: '{value}'. Expected one of: UNENCRYPTED, PSK, CERT")

    @classmethod
    def parse_modes(cls, mode_string: str) -> list["EncryptionMode"]:
        """Parse a comma-separated string of modes into a list of mode enums."""
        if not mode_string:
            return []
        tokens = [t.strip() for t in mode_string.split(",")]
        return [cls.from_string(t) for t in tokens if t]


class Encryption:
    _MODE_FIELDS = {
        EncryptionMode.PSK: ("psk_identity", "psk"),
        EncryptionMode.CERT: ("issuer", "subject"),
    }

    def __init__(self, connect_unencrypted: bool = False, accept_unencrypted: bool = False):
        self.connect = [EncryptionMode.UNENCRYPTED] if connect_unencrypted else []
        self.accept = [EncryptionMode.UNENCRYPTED] if accept_unencrypted else []

        self.psk_identity = None
        self.psk = None
        self.issuer = None
        self.subject = None

    def _enable_mode(self, mode, connect, accept):
        if connect and mode not in self.connect:
            self.connect.append(mode)
        if accept and mode not in self.accept:
            self.accept.append(mode)
        return connect or accept

    def set_psk(self, connect: bool = True, accept: bool = True,
                identity: str = None, psk: str = None):
        if self._enable_mode(EncryptionMode.PSK, connect, accept):
            if not identity or not psk:
                raise ValueError("set_psk requires both 'identity' and 'psk'.")
            self.psk_identity = identity
            self.psk = psk
        return self

    def set_cert(self, connect: bool = True, accept: bool = True,
                 issuer: str = None, subject: str = None):
        if self._enable_mode(EncryptionMode.CERT, connect, accept):
            if not issuer and not subject:
                raise ValueError("set_cert requires at least 'issuer' or 'subject'.")
            self.issuer = issuer
            self.subject = subject
        return self

    @staticmethod
    def _modes_to_string(modes: list[EncryptionMode]) -> str:
        return ", ".join(m.name for m in modes)

    def to_dict(self) -> dict:
        result = {}
        if self.connect:
            result["connect"] = self._modes_to_string(self.connect)
        if self.accept:
            result["accept"] = self._modes_to_string(self.accept)
        for fields in self._MODE_FIELDS.values():
            for field in fields:
                value = getattr(self, field)
                if value is not None:
                    result[field] = value
        return result

    def check(self, label: str = "Encryption"):
        if not self.connect:
            raise ValueError(f"{label}: no connect mode configured.")
        if not self.accept:
            raise ValueError(f"{label}: no accept mode configured.")

        all_modes = self.connect + self.accept
        for mode, fields in self._MODE_FIELDS.items():
            values = {f: getattr(self, f) for f in fields}
            if mode in all_modes:
                if not all(values.values()):
                    names = " and ".join(repr(f) for f in fields)
                    raise ValueError(f"{label}: {names} are required when {mode.name} mode is enabled.")
            else:
                for f, v in values.items():
                    if v is not None:
                        raise ValueError(f"{label}: {f!r} provided but {mode.name} not enabled in connect or accept.")


class HostEncryption(DictEntity, Encryption):
    """Host-level encryption settings applied through the Zabbix API."""

    _SCHEMA = [
        SchemaField("host", optional=False, description="Zabbix host technical name to update."),
        SchemaField("connect", optional=False, description="Comma-separated encryption modes used for outbound connections: UNENCRYPTED, PSK, or CERT."),
        SchemaField("accept", optional=False, description="Comma-separated encryption modes accepted by the host: UNENCRYPTED, PSK, or CERT."),
        SchemaField("psk_identity", description="PSK identity required when PSK mode is enabled."),
        SchemaField("psk", description="PSK secret required when PSK mode is enabled."),
        SchemaField("issuer", description="TLS certificate issuer required with subject when CERT mode is enabled."),
        SchemaField("subject", description="TLS certificate subject required with issuer when CERT mode is enabled."),
    ]

    def __init__(self, host, connect_unencrypted: bool = False, accept_unencrypted: bool = False):
        from zbxtemplar.zabbix.Host import Host
        self.host = host.host if isinstance(host, Host) else host
        super().__init__(connect_unencrypted, accept_unencrypted)

    @classmethod
    def from_encryption(cls, host: str, encryption: Encryption) -> "HostEncryption":
        entry = cls.__new__(cls)
        entry.__dict__ = copy.deepcopy(encryption.__dict__)
        entry.host = host
        return entry

    def to_dict(self) -> dict:
        result = {"host": self.host}
        result.update(super().to_dict())
        return result

    def check(self, label: str = None):
        super().check(label or f"Host '{self.host}'")

    @classmethod
    def from_dict(cls, data: dict) -> "HostEncryption":
        cls.validate(data)
        host_name = data["host"]

        entry = cls(host_name)
        entry.connect = EncryptionMode.parse_modes(data["connect"])
        entry.accept = EncryptionMode.parse_modes(data["accept"])

        all_modes = set(entry.connect + entry.accept)
        for mode, fields in cls._MODE_FIELDS.items():
            if mode in all_modes:
                for field in fields:
                    setattr(entry, field, data.get(field))

        entry.check()
        return entry
