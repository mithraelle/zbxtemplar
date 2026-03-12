from zbxtemplar.core.DecreeEntity import DecreeEntity, _validate
from zbxtemplar.core.constants import GuiAccess, Permission


class UserGroup(DecreeEntity):
    def __init__(self, name: str, gui_access: GuiAccess = None):
        self.name = name
        self.gui_access = gui_access
        self.host_groups = []
        self.template_groups = []

    def set_gui_access(self, gui_access: GuiAccess):
        self.gui_access = gui_access
        return self

    def add_host_group(self, name: str, permission: Permission):
        if not any(hg["name"] == name for hg in self.host_groups):
            self.host_groups.append({"name": name, "permission": permission})
        return self

    def add_template_group(self, name: str, permission: Permission):
        if not any(tg["name"] == name for tg in self.template_groups):
            self.template_groups.append({"name": name, "permission": permission})
        return self

    @classmethod
    def from_dict(cls, data: dict):
        gui = data.get("gui_access")
        if gui is not None:
            _validate(gui, GuiAccess._API_VALUES, "gui_access")
        group = cls(data["name"], gui_access=gui)
        for hg in data.get("host_groups", []):
            _validate(hg["permission"], Permission._API_VALUES, "permission")
            group.add_host_group(hg["name"], hg["permission"])
        for tg in data.get("template_groups", []):
            _validate(tg["permission"], Permission._API_VALUES, "permission")
            group.add_template_group(tg["name"], tg["permission"])
        return group