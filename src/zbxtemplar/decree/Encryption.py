import copy

from zbxtemplar.dicts.Schema import ApiStrEnum, Schema, SchemaField


class EncryptionMode(ApiStrEnum):
    """Zabbix host communication encryption mode: UNENCRYPTED, PSK, or CERT."""

    UNENCRYPTED = "UNENCRYPTED", 1
    PSK         = "PSK",         2
    CERT        = "CERT",        4


class Encryption(Schema):
    """Zabbix host-communication encryption settings: modes plus PSK/CERT credentials."""

    _SCHEMA = [
        SchemaField("connect", type=list[EncryptionMode],
                    description="Comma-separated encryption modes used for outbound connections: UNENCRYPTED, PSK, or CERT."),
        SchemaField("accept", type=list[EncryptionMode],
                    description="Comma-separated encryption modes accepted by the host: UNENCRYPTED, PSK, or CERT."),
        SchemaField("psk_identity", description="PSK identity required when PSK mode is enabled."),
        SchemaField("psk", description="PSK secret required when PSK mode is enabled."),
        SchemaField("issuer", description="TLS certificate issuer required with subject when CERT mode is enabled."),
        SchemaField("subject", description="TLS certificate subject required with issuer when CERT mode is enabled."),
    ]

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
        """Enable PSK encryption mode. Both identity and psk are required.

        Args:
            connect: Use PSK for outbound connections.
            accept: Accept PSK for inbound connections.
            identity: PSK identity string.
            psk: PSK secret value.
        """
        if self._enable_mode(EncryptionMode.PSK, connect, accept):
            if not identity or not psk:
                raise ValueError("set_psk requires both 'identity' and 'psk'.")
            self.psk_identity = identity
            self.psk = psk
        return self

    def set_cert(self, connect: bool = True, accept: bool = True,
                 issuer: str = None, subject: str = None):
        """Enable certificate encryption mode. At least one of issuer or subject is required.

        Args:
            connect: Use cert for outbound connections.
            accept: Accept cert for inbound connections.
            issuer: TLS certificate issuer (optional).
            subject: TLS certificate subject (optional).
        """
        if self._enable_mode(EncryptionMode.CERT, connect, accept):
            if not issuer and not subject:
                raise ValueError("set_cert requires at least 'issuer' or 'subject'.")
            self.issuer = issuer
            self.subject = subject
        return self

    @staticmethod
    def _modes_to_string(modes: list[EncryptionMode]) -> str:
        return ", ".join(m.value for m in modes)

    def connect_to_list(self):
        return self._modes_to_string(self.connect) if self.connect else None

    def accept_to_list(self):
        return self._modes_to_string(self.accept) if self.accept else None

    def _label(self) -> str:
        return "Encryption"

    def check(self) -> None:
        label = self._label()
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


class HostEncryption(Encryption):
    """Host-level encryption settings applied through the Zabbix API."""

    _SCHEMA = [
        SchemaField("host", optional=False, description="Zabbix host technical name to update."),
        SchemaField("connect", type=list[EncryptionMode], description="Comma-separated encryption modes used for outbound connections: UNENCRYPTED, PSK, or CERT."),
        SchemaField("accept", type=list[EncryptionMode], description="Comma-separated encryption modes accepted by the host: UNENCRYPTED, PSK, or CERT."),
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

    def _label(self) -> str:
        return f"Host '{self.host}'"

