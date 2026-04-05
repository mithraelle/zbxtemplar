from typing import Self

from zbxtemplar.decree.Action import Action
from zbxtemplar.decree.Encryption import Encryption, HostEncryption
from zbxtemplar.decree.User import User
from zbxtemplar.decree.UserGroup import UserGroup
from zbxtemplar.modules.Context import Context
from zbxtemplar.zabbix.Host import Host


class DecreeModule:
    def __init__(self, context: Context | None = None):
        self.context = context
        self.user_groups: list[UserGroup] = []
        self.users: list[User] = []
        self.actions: list[Action] = []
        self.encryption_defaults: Encryption | None = None
        self.encryptions: list[HostEncryption] = []

    def add_user_group(self, group: UserGroup) -> Self:
        if any(g.name == group.name for g in self.user_groups):
            return self
        self.user_groups.append(group)
        return self

    def add_user(self, user: User) -> Self:
        if any(u.username == user.username for u in self.users):
            return self
        self.users.append(user)
        return self

    def add_action(self, action: Action) -> Self:
        if any(a.name == action.name for a in self.actions):
            return self
        self.actions.append(action)
        return self

    def set_encryption_defaults(self, defaults: Encryption) -> Self:
        self.encryption_defaults = defaults
        return self

    def add_host_encryption(self, host: Host | str, encryption: Encryption) -> Self:
        name = host.host if isinstance(host, Host) else str(host)
        if any(e.host == name for e in self.encryptions):
            return self
        self.encryptions.append(HostEncryption.from_encryption(name, encryption))
        return self

    def export_user_groups(self) -> dict:
        if not self.user_groups:
            return {}
        return {"user_group": [g.to_dict() for g in self.user_groups]}

    def export_users(self) -> dict:
        if not self.users:
            return {}
        return {"add_user": [u.to_dict() for u in self.users]}

    def export_actions(self) -> dict:
        if not self.actions:
            return {}
        return {"actions": [a.to_dict() for a in self.actions]}

    def export_encryption(self) -> dict:
        if not self.encryptions and not self.encryption_defaults:
            return {}
        enc = {}
        if self.encryption_defaults:
            enc["host_defaults"] = self.encryption_defaults.to_dict()
        if self.encryptions:
            enc["hosts"] = [e.to_dict() for e in self.encryptions]
        return {"encryption": enc}

    def to_export(self) -> dict:
        result = {}
        result.update(self.export_user_groups())
        result.update(self.export_users())
        result.update(self.export_actions())
        result.update(self.export_encryption())
        return result