from zbxtemplar.dicts.Schema import ApiStrEnum, SchemaField
from zbxtemplar.decree.DecreeEntity import DecreeEntity
from zbxtemplar.decree.Token import Token
from zbxtemplar.decree.constants import ActiveStatus


class Severity(ApiStrEnum):
    """Trigger severity levels."""
    NOT_CLASSIFIED = "NOT_CLASSIFIED", 1
    INFORMATION    = "INFORMATION",    2
    WARNING        = "WARNING",        4
    AVERAGE        = "AVERAGE",        8
    HIGH           = "HIGH",           16
    DISASTER       = "DISASTER",       32

    @staticmethod
    def mask(severities: list) -> int:
        mask = 0
        for s in severities:
            mask |= Severity(s).api
        return mask

from zbxtemplar.decree.UserGroup import UserGroup


class UserMedia(DecreeEntity):
    """Notification media configuration for a managed user."""

    _SCHEMA = [
        SchemaField("type", optional=False, type=str, api_key="mediatypeid",
                    description="Zabbix media type name."),
        SchemaField("sendto", optional=False, type=str, description="Recipient address or target for the media type."),
        SchemaField("active", str_type="ENABLED or DISABLED", type=ActiveStatus,
                    description="Whether the media is enabled."),
        SchemaField("severity", type=list[Severity], str_type="list[Severity]",
                    description="Enabled trigger severities."),
        SchemaField("period", type=str, description="Zabbix media active time period, for example 1-7,00:00-24:00."),
    ]

    def __init__(self, media_type: str, sendto: str):
        self.type = media_type
        self.sendto = sendto

    def set_severity(self, severity: list):
        """Set which trigger severities activate this media. Pass a list of Severity constants."""
        self.severity = severity
        return self

    def set_period(self, period: str):
        """Set the active time window, e.g. ``"1-7,00:00-24:00"``."""
        self.period = period
        return self

    def severity_to_list(self):
        return ",".join(self.severity)


class User(DecreeEntity):
    """Zabbix user account managed by decree YAML."""

    _SCHEMA = [
        SchemaField("username", optional=False, type=str, description="Zabbix username."),
        SchemaField("role", optional=False, type=str, api_key="roleid",
                    description="Zabbix role name assigned to the user."),
        SchemaField("password", type=str, description="Password to set when creating or updating the user."),
        SchemaField("groups", type=list[str], str_type="list[str]", api_key="usrgrps",
                    description="User group names to attach to the user."),
        SchemaField("medias", type=list[UserMedia], str_type="list[UserMedia]", description="Media definitions for the user."),
        SchemaField("token", type=Token, str_type="Token", description="API token provisioning configuration for the user."),
        SchemaField("force_token", type=bool, str_type="bool", description="Update and re-generate an existing token with the same name."),
    ]

    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role
        self.password = None
        self.groups = []
        self.medias = []
        self.token = None
        self.force_token = None

    def set_password(self, password: str):
        """Set the login password. Supports env-var placeholder syntax, e.g. ``"${ZBX_PASSWORD}"``."""
        self.password = password
        return self

    def link_group(self, group):
        """Assign to a user group. Accepts a UserGroup object or name string. Raises on duplicate."""
        name = group.name if isinstance(group, UserGroup) else group
        if name in self.groups:
            raise ValueError(
                f"Duplicate group '{name}' on user '{self.username}'"
            )
        self.groups.append(name)
        return self

    def add_media(self, media_type: str, sendto: str, severity: list | None = None, period: str | None = None) -> "UserMedia":
        """Create and attach a notification media entry. Returns the created UserMedia."""
        media = UserMedia(media_type, sendto)
        if severity is not None:
            media.set_severity(severity)
        if period is not None:
            media.set_period(period)
        self.medias.append(media)
        return media

    def set_token(self, name: str, store_at, expires_at=None, force: bool = False) -> Token:
        """Create and provision an API token for this user. Returns the created Token."""
        self.token = Token(name, store_at=store_at, expires_at=expires_at)
        if force:
            self.force_token = True
        return self.token

    def _wire_up(self) -> None:
        if self.groups is None:
            self.groups = []
        else:
            seen = set()
            for g in self.groups:
                if g in seen:
                    raise ValueError(f"Duplicate group '{g}' on user '{self.username}'")
                seen.add(g)
        if self.medias is None:
            self.medias = []
