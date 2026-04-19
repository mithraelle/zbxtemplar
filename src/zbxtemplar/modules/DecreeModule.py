from zbxtemplar.decree.Action import Action, AutoregistrationAction, TriggerAction
from zbxtemplar.decree.Encryption import Encryption, HostEncryption
from zbxtemplar.decree.saml import SamlProvider
from zbxtemplar.decree.User import User
from zbxtemplar.decree.UserGroup import UserGroup
from zbxtemplar.modules.BaseModule import BaseModule
from zbxtemplar.zabbix.Host import Host


class DecreeModule(BaseModule):
    def __init__(self, **kwargs):
        self.user_groups: list[UserGroup] = []
        self.saml: SamlProvider | None = None
        self.users: list[User] = []
        self.actions: list[Action] = []
        self.encryption_defaults: Encryption | None = None
        self.encryptions: list[HostEncryption] = []
        super().__init__(**kwargs)

    def add_user_group(
        self,
        name: str,
        gui_access: str | None = None,
        users_status: str | None = None,
    ) -> UserGroup:
        if any(g.name == name for g in self.user_groups):
            raise ValueError(
                f"{type(self).__name__}: duplicate user group '{name}'"
            )
        group = UserGroup(name=name, gui_access=gui_access, users_status=users_status)
        self.user_groups.append(group)
        return group

    def add_user(self, username: str, role: str) -> User:
        if any(u.username == username for u in self.users):
            raise ValueError(
                f"{type(self).__name__}: duplicate user '{username}'"
            )
        user = User(username=username, role=role)
        self.users.append(user)
        return user

    def set_saml(
        self,
        idp_entityid: str,
        sp_entityid: str,
        sso_url: str,
        username_attribute: str,
        slo_url: str | None = None,
    ) -> SamlProvider:
        if self.saml is not None:
            raise ValueError(
                f"{type(self).__name__}: SAML provider already configured"
            )
        provider = SamlProvider(
            idp_entityid=idp_entityid,
            sp_entityid=sp_entityid,
            sso_url=sso_url,
            username_attribute=username_attribute,
            slo_url=slo_url,
        )
        self.saml = provider
        return provider

    def _add_action(self, action: Action) -> Action:
        if any(a.name == action.name for a in self.actions):
            raise ValueError(
                f"{type(self).__name__}: duplicate action '{action.name}'"
            )
        self.actions.append(action)
        return action

    def add_trigger_action(self, name: str) -> TriggerAction:
        action = TriggerAction(name)
        self._add_action(action)
        return action

    def add_autoregistration_action(self, name: str) -> AutoregistrationAction:
        action = AutoregistrationAction(name)
        self._add_action(action)
        return action

    def set_encryption_defaults(
        self,
        connect_unencrypted: bool = False,
        accept_unencrypted: bool = False,
    ) -> Encryption:
        defaults = Encryption(
            connect_unencrypted=connect_unencrypted,
            accept_unencrypted=accept_unencrypted,
        )
        self.encryption_defaults = defaults
        return defaults

    def add_host_encryption(
        self,
        host: Host | str,
        connect_unencrypted: bool = False,
        accept_unencrypted: bool = False,
    ) -> HostEncryption:
        name = host.host if isinstance(host, Host) else str(host)
        if any(e.host == name for e in self.encryptions):
            raise ValueError(
                f"{type(self).__name__}: duplicate host encryption for '{name}'"
            )
        encryption = HostEncryption(
            host=name,
            connect_unencrypted=connect_unencrypted,
            accept_unencrypted=accept_unencrypted,
        )
        self.encryptions.append(encryption)
        return encryption

    def export_user_groups(self) -> dict:
        if not self.user_groups:
            return {}
        return {"user_group": [g.to_dict() for g in self.user_groups]}

    def export_users(self) -> dict:
        if not self.users:
            return {}
        return {"add_user": [u.to_dict() for u in self.users]}

    def export_saml(self) -> dict:
        if not self.saml:
            return {}
        return {"saml": self.saml.to_dict()}

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
        result.update(self.export_macros())
        result.update(self.export_user_groups())
        result.update(self.export_saml())
        result.update(self.export_users())
        result.update(self.export_actions())
        result.update(self.export_encryption())
        return result
