from zbxtemplar.dicts.Schema import ApiStrEnum, field, SubsetBy
from zbxtemplar.decree.DecreeEntity import DecreeEntity
from zbxtemplar.zabbix.Host import HostGroup
from zbxtemplar.zabbix.Template import TemplateGroup


class GuiAccess(ApiStrEnum):
    """User group GUI access modes."""
    DEFAULT  = "DEFAULT",  0
    INTERNAL = "INTERNAL", 1
    LDAP     = "LDAP",     2
    DISABLED = "DISABLED", 3


class UsersStatus(ApiStrEnum):
    """User group users status (whether member users are enabled)."""
    ENABLED  = "ENABLED",  0
    DISABLED = "DISABLED", 1


class Permission(ApiStrEnum):
    """Host/template group permission levels."""
    NONE       = "NONE",       0
    READ       = "READ",       2
    READ_WRITE = "READ_WRITE", 3


class PermissionGroup(DecreeEntity):
    """Host or template group permission entry on a UserGroup."""

    name: str = field(
        optional=False,
        description="Host or template group name.",
    )
    permission: Permission = field(
        optional=False,
        str_type="Permission",
        description="Permission level: NONE, READ, or READ_WRITE.",
    )

    def __init__(self, name: str, permission: Permission):
        self.name = name
        self.permission = permission


class UserGroup(DecreeEntity):
    """Zabbix user group and permission mapping managed by decree YAML."""

    name: str = field(
        optional=False,
        description="Zabbix user group name.",
    )
    gui_access: GuiAccess | None = field(
        str_type="GuiAccess",
        description="GUI access mode: DEFAULT, INTERNAL, LDAP, or DISABLED.",
    )
    users_status: UsersStatus | None = field(
        str_type="UsersStatus",
        description="Member users status: ENABLED or DISABLED.",
        api_default="ENABLED",
    )
    host_groups: list[PermissionGroup] = field(
        str_type="list[PermissionGroup]",
        api_key="hostgroup_rights",
        default=[],
        policy=SubsetBy("name"),
        description="Host group permission entries with name and permission.",
    )
    template_groups: list[PermissionGroup] = field(
        str_type="list[PermissionGroup]",
        api_key="templategroup_rights",
        default=[],
        policy=SubsetBy("name"),
        description="Template group permission entries with name and permission.",
    )

    def __init__(self, name: str, gui_access: GuiAccess | None = None, users_status: UsersStatus | None = None):
        self.name = name
        self.gui_access = gui_access
        self.users_status = users_status

    def set_gui_access(self, gui_access: GuiAccess):
        """Set GUI access mode. Use GuiAccess constants: DEFAULT, INTERNAL, LDAP, DISABLED."""
        self.gui_access = gui_access
        return self

    def set_users_status(self, users_status: UsersStatus):
        """Set whether member users are active. Use UsersStatus constants: ENABLED, DISABLED."""
        self.users_status = users_status
        return self

    def link_host_group(self, group: HostGroup | str, permission: Permission):
        """Grant permission to a host group. Accepts HostGroup object or name string. Raises on duplicate."""
        name = group.name if isinstance(group, HostGroup) else group
        if any(pg.name == name for pg in self.host_groups):
            raise ValueError(
                f"Duplicate host_group '{name}' on user group '{self.name}'"
            )
        self.host_groups.append(PermissionGroup(name, permission))
        return self

    def link_template_group(self, group: TemplateGroup | str, permission: Permission):
        """Grant permission to a template group. Accepts TemplateGroup object or name string. Raises on duplicate."""
        name = group.name if isinstance(group, TemplateGroup) else group
        if any(pg.name == name for pg in self.template_groups):
            raise ValueError(
                f"Duplicate template_group '{name}' on user group '{self.name}'"
            )
        self.template_groups.append(PermissionGroup(name, permission))
        return self

    @classmethod
    def from_data(cls, data):
        if isinstance(data, str):
            return cls(data)
        return super().from_data(data)