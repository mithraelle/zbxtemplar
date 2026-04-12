from zbxtemplar.DictEntity import DictEntity, SchemaField
from zbxtemplar.decree.DecreeEntity import DecreeEntity, _validate
from zbxtemplar.zabbix.Host import HostGroup
from zbxtemplar.zabbix.Template import TemplateGroup


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


class UserGroup(DecreeEntity, DictEntity):
    """Zabbix user group and permission mapping managed by decree YAML."""

    _SCHEMA = [
        SchemaField("name", optional=False, description="Zabbix user group name."),
        SchemaField("gui_access", description="GUI access mode: DEFAULT, INTERNAL, LDAP, or DISABLED."),
        SchemaField("host_groups", str_type="list[dict]", description="Host group permission entries with name and permission."),
        SchemaField("template_groups", str_type="list[dict]", description="Template group permission entries with name and permission."),
    ]

    def __init__(self, name: str, gui_access: GuiAccess = None):
        self.name = name
        self.gui_access = gui_access
        self.host_groups = []
        self.template_groups = []

    def set_gui_access(self, gui_access: GuiAccess):
        self.gui_access = gui_access
        return self

    def add_host_group(self, group, permission: Permission):
        name = group.name if isinstance(group, HostGroup) else group
        if any(hg["name"] == name for hg in self.host_groups):
            raise ValueError(
                f"Duplicate host_group '{name}' on user group '{self.name}'"
            )
        self.host_groups.append({"name": name, "permission": permission})
        return self

    def add_template_group(self, group, permission: Permission):
        name = group.name if isinstance(group, TemplateGroup) else group
        if any(tg["name"] == name for tg in self.template_groups):
            raise ValueError(
                f"Duplicate template_group '{name}' on user group '{self.name}'"
            )
        self.template_groups.append({"name": name, "permission": permission})
        return self

    @classmethod
    def from_dict(cls, data: dict, host_groups=None, template_groups=None):
        cls.validate(data)
        gui = data.get("gui_access")
        if gui is not None:
            _validate(gui, GuiAccess._API_VALUES, "gui_access")
        group = cls(data["name"], gui_access=gui)
        for hg in data.get("host_groups", []):
            _validate(hg["permission"], Permission._API_VALUES, "permission")
            group.add_host_group(hg["name"], hg["permission"])
            if host_groups is not None and hg["name"] not in host_groups:
                host_groups[hg["name"]] = HostGroup(hg["name"])
        for tg in data.get("template_groups", []):
            _validate(tg["permission"], Permission._API_VALUES, "permission")
            group.add_template_group(tg["name"], tg["permission"])
            if template_groups is not None and tg["name"] not in template_groups:
                template_groups[tg["name"]] = TemplateGroup(tg["name"])
        return group
