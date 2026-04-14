from enum import Enum

from zbxtemplar.dicts.DictEntity import DictEntity


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


def _validate(value, allowed, label):
    if value not in allowed:
        raise ValueError(f"Invalid {label} '{value}', expected one of: {', '.join(allowed)}")


class DecreeEntity(DictEntity):
    _OMIT_FROM_SCHEMA_DOCS = True

    def to_dict(self) -> dict:
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            if value is None or value == {} or value == []:
                continue
            list_method = getattr(self, f'{key}_to_list', None)
            if list_method:
                items = list_method()
                if items:
                    result[key] = items
            elif hasattr(value, 'to_dict'):
                items = value.to_dict()
                if items:
                    result[key] = items
            elif isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result
