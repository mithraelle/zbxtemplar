from zbxtemplar.decree.Encryption import HostEncryption
from zbxtemplar.decree.saml import SamlProvider
from zbxtemplar.decree.Token import Token
from zbxtemplar.decree.User import User
from zbxtemplar.decree.UserGroup import UserGroup
from zbxtemplar.zabbix.ZbxEntity import YesNo


_SAML_IDP_TYPE = 2


class APIContext:
    """Registry of entities pulled live from a Zabbix API connection."""

    def __init__(self, api):
        self._api = api
        self._user_groups: dict[str, UserGroup] = {}
        self._users: dict[str, User] = {}
        self._saml: SamlProvider | None = None
        self._host_encryptions: dict[str, HostEncryption] = {}

        self._api_hostgroup_names: dict[str, str] = {}
        self._api_templategroup_names: dict[str, str] = {}
        self._api_usergroup_names: dict[str, str] = {}
        self._api_role_names: dict[str, str] = {}
        self._api_mediatype_names: dict[str, str] = {}

    def _get_hostgroup_names(self) -> dict[str, str]:
        if not self._api_hostgroup_names:
            self._api_hostgroup_names = {
                g["groupid"]: g["name"]
                for g in self._api.hostgroup.get(output=["groupid", "name"])
            }
        return self._api_hostgroup_names

    def _get_templategroup_names(self) -> dict[str, str]:
        if not self._api_templategroup_names:
            self._api_templategroup_names = {
                g["groupid"]: g["name"]
                for g in self._api.templategroup.get(output=["groupid", "name"])
            }
        return self._api_templategroup_names

    def _get_usergroup_names(self) -> dict[str, str]:
        if not self._api_usergroup_names:
            self._api_usergroup_names = {
                g["usrgrpid"]: g["name"]
                for g in self._api.usergroup.get(output=["usrgrpid", "name"])
            }
        return self._api_usergroup_names

    def _get_role_names(self) -> dict[str, str]:
        if not self._api_role_names:
            self._api_role_names = {
                r["roleid"]: r["name"]
                for r in self._api.role.get(output=["roleid", "name"])
            }
        return self._api_role_names

    def _get_mediatype_names(self) -> dict[str, str]:
        if not self._api_mediatype_names:
            self._api_mediatype_names = {
                m["mediatypeid"]: m["name"]
                for m in self._api.mediatype.get(output=["mediatypeid", "name"])
            }
        return self._api_mediatype_names

    def pull_user_groups(self, groups: list[str] | None = None):
        params: dict = {
            "output": ["name", "gui_access", "users_status"],
            "selectHostGroupRights": ["id", "permission"],
            "selectTemplateGroupRights": ["id", "permission"],
        }
        if groups is not None:
            params["filter"] = {"name": groups}

        raw_groups = self._api.usergroup.get(**params)
        hg_names = self._get_hostgroup_names()
        tg_names = self._get_templategroup_names()

        for raw in raw_groups:
            raw["hostgroup_rights"] = [
                {"name": hg_names[r["id"]], "permission": r["permission"]}
                for r in raw.get("hostgroup_rights") or [] if r["id"] in hg_names
            ]
            raw["templategroup_rights"] = [
                {"name": tg_names[r["id"]], "permission": r["permission"]}
                for r in raw.get("templategroup_rights") or [] if r["id"] in tg_names
            ]
            ug = UserGroup.from_api(raw)
            self._user_groups[ug.name] = ug
        return self

    def get_user_group(self, name: str) -> UserGroup:
        if name not in self._user_groups:
            raise ValueError(f"User group '{name}' not found in API context")
        return self._user_groups[name]

    def pull_users(self, users: list[str] | None = None):
        params: dict = {
            "output": ["userid", "username", "roleid"],
            "selectUsrgrps": ["name"],
            "selectMedias": ["mediatypeid", "sendto", "active", "severity", "period"],
        }
        if users is not None:
            params["filter"] = {"username": users}

        raw_users = self._api.user.get(**params)
        role_names = self._get_role_names()
        mediatype_names = self._get_mediatype_names()

        by_userid = {raw["userid"]: raw for raw in raw_users}
        if by_userid:
            tokens = self._api.token.get(
                userids=list(by_userid),
                output=["userid", "name", "expires_at"],
            )
            for t in tokens:
                raw = by_userid.get(t["userid"])
                if raw is None or "token" in raw:
                    continue
                raw["token"] = {
                    "name": t["name"],
                    "store_at": Token.STDOUT,
                    "expires_at": Token.EXPIRES_NEVER if str(t["expires_at"]) == "0" else int(t["expires_at"]),
                }

        for raw in raw_users:
            raw["roleid"] = role_names[raw["roleid"]]
            raw["usrgrps"] = [g["name"] for g in raw.get("usrgrps") or []]
            for m in raw.get("medias") or []:
                m["mediatypeid"] = mediatype_names[m["mediatypeid"]]
                if isinstance(m.get("sendto"), list):
                    m["sendto"] = ",".join(m["sendto"])
            u = User.from_api(raw)
            self._users[u.username] = u
        return self

    def get_user(self, name: str) -> User:
        if name not in self._users:
            raise ValueError(f"User '{name}' not found in API context")
        return self._users[name]

    def pull_saml(self):
        raw = self._api.userdirectory.get(
            filter={"idp_type": _SAML_IDP_TYPE},
            output="extend",
            selectProvisionGroups="extend",
            selectProvisionMedia="extend",
        )
        if not raw:
            self._saml = None
            return self
        raw_saml = raw[0]

        role_names = self._get_role_names()
        mediatype_names = self._get_mediatype_names()
        ugroup_names = self._get_usergroup_names()

        for field in SamlProvider._SCHEMA:
            if field.type is YesNo and field.key in raw_saml:
                raw_saml[field.key] = "YES" if str(raw_saml[field.key]) == "1" else "NO"

        for g in raw_saml.get("provision_groups") or []:
            g["role"] = role_names[g["roleid"]]
            g["user_groups"] = [
                ugroup_names[u["usrgrpid"]] for u in g.get("user_groups") or []
            ]
        for m in raw_saml.get("provision_media") or []:
            m["mediatypeid"] = mediatype_names[m["mediatypeid"]]

        auth = self._api.authentication.get(output="extend")
        if isinstance(auth, list):
            auth = auth[0] if auth else {}
        auth = auth or {}
        disabled = auth.get("disabled_usrgrpid")
        if disabled and str(disabled) != "0":
            raw_saml["disabled_user_group"] = ugroup_names.get(str(disabled))
        cs = auth.get("saml_case_sensitive")
        if cs is not None:
            raw_saml["saml_case_sensitive"] = "YES" if str(cs) == "1" else "NO"

        self._saml = SamlProvider.from_api(raw_saml)
        return self

    def get_saml(self) -> SamlProvider:
        if self._saml is None:
            raise ValueError("SAML config not found in API context")
        return self._saml

    def pull_host_encryption(self, hosts: list[str] | None = None):
        params: dict = {
            "output": [
                "host", "tls_connect", "tls_accept",
                "tls_issuer", "tls_subject", "tls_psk_identity",
            ],
        }
        if hosts is not None:
            params["filter"] = {"host": hosts}

        for raw in self._api.host.get(**params):
            payload = {
                "host": raw["host"],
                "connect": raw["tls_connect"],
                "accept": raw["tls_accept"],
            }
            for src, dst in (
                ("tls_psk_identity", "psk_identity"),
                ("tls_issuer", "issuer"),
                ("tls_subject", "subject"),
            ):
                value = raw.get(src)
                if value:
                    payload[dst] = value
            entry = HostEncryption.from_dict(payload)
            self._host_encryptions[entry.host] = entry
        return self

    def get_host_encryption(self, host: str) -> HostEncryption:
        if host not in self._host_encryptions:
            raise ValueError(f"Host encryption '{host}' not found in API context")
        return self._host_encryptions[host]