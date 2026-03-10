class MediaType:
    """Zabbix built-in media type names (as of 7.4)."""
    BREVIS_ONE = "Brevis.one"
    DISCORD = "Discord"
    EMAIL = "Email"
    EMAIL_HTML = "Email (HTML)"
    EVENT_DRIVEN_ANSIBLE = "Event-Driven Ansible"
    EXPRESS_MS = "Express.ms"
    GITHUB = "Github"
    GLPi = "GLPi"
    GMAIL = "Gmail"
    GMAIL_RELAY = "Gmail relay"
    ILERT = "iLert"
    ITOP = "iTop"
    JIRA = "Jira"
    JIRA_SERVICE_DESK = "Jira ServiceDesk"
    LINE = "Line"
    MANAGEENGINE_SERVICE_DESK = "ManageEngine ServiceDesk"
    MANTISBT = "MantisBT"
    MATTERMOST = "Mattermost"
    MS_TEAMS = "MS Teams"
    MS_TEAMS_WORKFLOW = "MS Teams Workflow"
    OFFICE365 = "Office365"
    OFFICE365_RELAY = "Office365 relay"
    OPSGENIE = "Opsgenie"
    OTRS = "OTRS"
    OTRS_CE = "OTRS CE"
    PAGERDUTY = "PagerDuty"
    PUSHOVER = "Pushover"
    REDMINE = "Redmine"
    ROCKET_CHAT = "Rocket.Chat"
    SERVICENOW = "ServiceNow"
    SIGNL4 = "SIGNL4"
    SLACK = "Slack"
    SMS = "SMS"
    SOLARWINDS_SERVICE_DESK = "SolarWinds Service Desk"
    SYSAID = "SysAid"
    TELEGRAM = "Telegram"
    TOPDESK = "TOPdesk"
    VICTOROPS = "VictorOps"
    ZAMMAD = "Zammad"
    ZENDESK = "Zendesk"


class UserRole:
    """Zabbix built-in user roles."""
    SUPER_ADMIN = "Super admin role"
    ADMIN = "Admin role"
    USER = "User role"
    GUEST = "Guest role"


class GuiAccess:
    """User group GUI access modes."""
    DEFAULT = "DEFAULT"
    INTERNAL = "INTERNAL"
    LDAP = "LDAP"
    DISABLED = "DISABLED"

    _API_VALUES = {"DEFAULT": 0, "INTERNAL": 1, "LDAP": 2, "DISABLED": 3}


class Permission:
    """Host/template group permission levels."""
    NONE = "NONE"
    READ = "READ"
    READ_WRITE = "READ_WRITE"

    _API_VALUES = {"NONE": 0, "READ": 2, "READ_WRITE": 3}


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


class MacroType:
    """Global macro types."""
    TEXT = "text"
    SECRET = "secret"
    VAULT = "vault"

    _API_VALUES = {"text": 0, "secret": 1, "vault": 2}