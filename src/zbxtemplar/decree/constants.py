from enum import IntEnum


class ProvisionStatus(IntEnum):
    """Zabbix SAML provisioning status values."""

    DISABLED = 0
    ENABLED = 1


class ScimStatus(IntEnum):
    """Zabbix SCIM provisioning status values."""

    DISABLED = 0
    ENABLED = 1


class ActiveStatus(IntEnum):
    """Enable/disable status values for decree entries."""

    ENABLED = 0
    DISABLED = 1
