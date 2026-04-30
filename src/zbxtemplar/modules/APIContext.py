from zbxtemplar.decree.Action import (
    Action, AutoregistrationAction, CONDITION_RESOLVERS, OP_LIST_TARGETS, OP_DICT_TARGETS,
)
from zbxtemplar.decree.Encryption import HostEncryption
from zbxtemplar.decree.saml import SamlProvider
from zbxtemplar.decree.Token import Token
from zbxtemplar.decree.User import User
from zbxtemplar.decree.UserGroup import UserGroup
from zbxtemplar.modules import Context
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
        self._actions: dict[str, Action] = {}

        self._api_id_name: dict[tuple, dict[str, str]] = {}

    @classmethod
    def from_context(cls, ctx: Context, api) -> "APIContext":
        api_ctx = cls(api)
        if ctx._user_groups:
            api_ctx.pull_user_groups(list(ctx._user_groups))
        if ctx._users:
            api_ctx.pull_users(list(ctx._users))
        if ctx._saml is not None:
            api_ctx.pull_saml()
        if ctx._host_encryptions:
            api_ctx.pull_host_encryption(list(ctx._host_encryptions))
        if ctx._actions:
            api_ctx.pull_actions(list(ctx._actions))
        return api_ctx

    def _id_name_map(self, api_name: str, id_field: str, name_field: str = "name") -> dict[str, str]:
        key = (api_name, id_field, name_field)
        if key not in self._api_id_name:
            items = getattr(self._api, api_name).get(output=[id_field, name_field])
            self._api_id_name[key] = {item[id_field]: item[name_field] for item in items}
        return self._api_id_name[key]

    def pull_user_groups(self, groups: list[str] | None = None):
        params: dict = {
            "output": ["name", "gui_access", "users_status"],
            "selectHostGroupRights": ["id", "permission"],
            "selectTemplateGroupRights": ["id", "permission"],
        }
        if groups is not None:
            params["filter"] = {"name": groups}

        raw_groups = self._api.usergroup.get(**params)
        hg_names = self._id_name_map("hostgroup", "groupid")
        tg_names = self._id_name_map("templategroup", "groupid")

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
        role_names = self._id_name_map("role", "roleid")
        mediatype_names = self._id_name_map("mediatype", "mediatypeid")

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

        role_names = self._id_name_map("role", "roleid")
        mediatype_names = self._id_name_map("mediatype", "mediatypeid")
        ugroup_names = self._id_name_map("usergroup", "usrgrpid")

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

    def pull_actions(self, names: list[str] | None = None):
        params: dict = {
            "output": [
                "actionid", "name", "eventsource", "status", "esc_period",
                "pause_symptoms", "pause_suppressed", "notify_if_canceled",
            ],
            "selectFilter": "extend",
            "selectOperations": "extend",
            "selectRecoveryOperations": "extend",
            "selectUpdateOperations": "extend",
        }
        if names is not None:
            params["filter"] = {"name": names}

        for raw in self._api.action.get(**params):
            raw["eventsource"] = int(raw["eventsource"])

            f = raw.get("filter") or {}
            if "evaltype" in f:
                f["evaltype"] = int(f["evaltype"])
            for cond in f.get("conditions") or []:
                ctype = int(cond.get("conditiontype", -1))
                cond["conditiontype"] = ctype
                if ctype in CONDITION_RESOLVERS:
                    api_name, id_field, _ = CONDITION_RESOLVERS[ctype]
                    names_map = self._id_name_map(api_name, id_field)
                    if cond.get("value") in names_map:
                        cond["value"] = names_map[cond["value"]]
            if f.get("conditions"):
                f["conditions"].sort(key=lambda c: c.get("formulaid", ""))

            for op_key in ("operations", "recovery_operations", "update_operations"):
                for op in raw.get(op_key) or []:
                    self._translate_action_op(op)
                    if raw["eventsource"] == AutoregistrationAction.eventsource:
                        for k in ("esc_step_from", "esc_step_to", "esc_period"):
                            op.pop(k, None)

            action = Action.from_dict(raw)
            self._actions[action.name] = action
        return self

    def _translate_action_op(self, op: dict) -> None:
        if "operationtype" in op:
            op["operationtype"] = int(op["operationtype"])
        for k in ("esc_step_from", "esc_step_to"):
            if k in op:
                op[k] = int(op[k])
        if "esc_period" in op:
            v = op["esc_period"]
            if isinstance(v, str) and v.isdigit():
                op["esc_period"] = int(v)

        for parent, id_field, api_name, name_field, _label in OP_LIST_TARGETS:
            if parent not in op:
                continue
            lookup = self._id_name_map(api_name, id_field, name_field)
            for entry in op[parent]:
                if entry.get(id_field) in lookup:
                    entry[id_field] = lookup[entry[id_field]]

        for parent, id_field, api_name, name_field, _label in OP_DICT_TARGETS:
            if parent not in op:
                continue
            value = op[parent].get(id_field)
            if value in (None, "", "0", 0):
                op[parent].pop(id_field, None)
                continue
            lookup = self._id_name_map(api_name, id_field, name_field)
            if value in lookup:
                op[parent][id_field] = lookup[value]

        if "opmessage" in op:
            msg = op["opmessage"]
            for k in ("subject", "message"):
                if msg.get(k) == "":
                    msg.pop(k)

        if "opinventory" in op and "inventory_mode" in op["opinventory"]:
            op["opinventory"]["inventory_mode"] = int(op["opinventory"]["inventory_mode"])

    def get_action(self, name: str) -> Action:
        if name not in self._actions:
            raise ValueError(f"Action '{name}' not found in API context")
        return self._actions[name]