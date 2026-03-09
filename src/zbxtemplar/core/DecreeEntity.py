class DecreeEntity:
    def to_dict(self) -> dict:
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            if value is None or value == {} or value == []:
                continue
            list_method = getattr(self, f'{key}_to_list', None)
            if list_method:
                result[key] = list_method()
            else:
                result[key] = value
        return result


class UserGroup(DecreeEntity):
    def __init__(self, name: str, gui_access: str = None):
        self.name = name
        self.gui_access = gui_access
        self.host_groups = []
        self.template_groups = []

    def add_host_group(self, name: str, permission: str):
        if not any(hg["name"] == name for hg in self.host_groups):
            self.host_groups.append({"name": name, "permission": permission})
        return self

    def add_template_group(self, name: str, permission: str):
        if not any(tg["name"] == name for tg in self.template_groups):
            self.template_groups.append({"name": name, "permission": permission})
        return self


class User(DecreeEntity):
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
        if name not in self.groups:
            self.groups.append(name)
        return self

    def add_media(self, media_type: str, sendto: str, severity: str = None, period: str = None):
        media = {"type": media_type, "sendto": sendto}
        if severity is not None:
            media["severity"] = severity
        if period is not None:
            media["period"] = period
        self.medias.append(media)
        return self

    def set_token(self, token: str, force: bool = False):
        self.token = token
        if force:
            self.force_token = True
        return self