from zbxtemplar.dicts.DictEntity import DictEntity, SchemaField
from zbxtemplar.decree.DecreeEntity import DecreeEntity, _validate
from zbxtemplar.decree.Token import Token


class Severity:
    """Trigger severity levels."""
    NOT_CLASSIFIED = "NOT_CLASSIFIED"
    INFORMATION = "INFORMATION"
    WARNING = "WARNING"
    AVERAGE = "AVERAGE"
    HIGH = "HIGH"
    DISASTER = "DISASTER"

    _API_VALUES = {
        "NOT_CLASSIFIED": 1, "INFORMATION": 2, "WARNING": 4,
        "AVERAGE": 8, "HIGH": 16, "DISASTER": 32,
    }

    @staticmethod
    def mask(severities: list) -> int:
        mask = 0
        for s in severities:
            mask |= Severity._API_VALUES[s]
        return mask
from zbxtemplar.decree.UserGroup import UserGroup


class UserMedia(DictEntity):
    """Notification media configuration for a managed user."""

    _SCHEMA = [
        SchemaField("type", optional=False, description="Zabbix media type name."),
        SchemaField("sendto", optional=False, description="Recipient address or target for the media type."),
        SchemaField("severity", str_type="list[str] | str", description="Enabled trigger severities as a list or comma-separated string."),
        SchemaField("period", description="Zabbix media active time period, for example 1-7,00:00-24:00."),
    ]

    def __init__(self, media_type: str, sendto: str):
        self.type = media_type
        self.sendto = sendto
        self.severity = None
        self.period = None

    def set_severity(self, severity: list):
        self.severity = severity
        return self

    def set_period(self, period: str):
        self.period = period
        return self

    def to_dict(self) -> dict:
        result = {"type": self.type, "sendto": self.sendto}
        if self.severity is not None:
            result["severity"] = ",".join(self.severity)
        if self.period is not None:
            result["period"] = self.period
        return result

    @classmethod
    def from_dict(cls, data: dict):
        cls.validate(data)
        media = cls(data["type"], data["sendto"])
        severity = data.get("severity")
        if severity is not None:
            if isinstance(severity, str):
                severity = severity.split(",")
            for s in severity:
                _validate(s, Severity._API_VALUES, "severity")
            media.set_severity(severity)
        if "period" in data:
            media.set_period(data["period"])
        return media


class User(DecreeEntity, DictEntity):
    """Zabbix user account managed by decree YAML."""

    _SCHEMA = [
        SchemaField("username", optional=False, description="Zabbix username."),
        SchemaField("role", optional=False, description="Zabbix role name assigned to the user."),
        SchemaField("password", description="Password to set when creating or updating the user."),
        SchemaField("groups", str_type="list[str]", description="User group names to attach to the user."),
        SchemaField("medias", str_type="list[UserMedia]", description="Media definitions for the user."),
        SchemaField("token", str_type="Token", description="API token provisioning configuration for the user."),
        SchemaField("force_token", str_type="bool", description="Update and re-generate an existing token with the same name."),
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
        self.password = password
        return self

    def add_group(self, group):
        name = group.name if isinstance(group, UserGroup) else group
        if name in self.groups:
            raise ValueError(
                f"Duplicate group '{name}' on user '{self.username}'"
            )
        self.groups.append(name)
        return self

    def add_media(self, media: UserMedia):
        self.medias.append(media)
        return self

    def set_token(self, token: Token, force: bool = False):
        if not isinstance(token, Token):
            raise ValueError("token must be a Token")
        self.token = token
        if force:
            self.force_token = True
        return self

    def medias_to_list(self):
        return [m.to_dict() for m in self.medias]

    @classmethod
    def from_dict(cls, data: dict, user_groups=None):
        cls.validate(data)
        user = cls(data["username"], data["role"])
        if "password" in data:
            user.set_password(data["password"])
        for g in data.get("groups", []):
            user.add_group(g)
            if user_groups is not None and g not in user_groups:
                user_groups[g] = UserGroup(g)
        for m in data.get("medias", []):
            user.add_media(UserMedia.from_dict(m))
        if "token" in data:
            user.set_token(Token.from_dict(data["token"]), force=data.get("force_token", False))
        return user
