from zbxtemplar.decree.Token import Token
from zbxtemplar.decree.User import User
from zbxtemplar.decree.UserGroup import UserGroup


class APIContext:
    """Registry of entities pulled live from a Zabbix API connection."""

    def __init__(self, api):
        self._api = api
        self._user_groups: dict[str, UserGroup] = {}
        self._users: dict[str, User] = {}
        self._hostgroup_names: dict[str, str] = {}
        self._templategroup_names: dict[str, str] = {}
        self._role_names: dict[str, str] = {}
        self._mediatype_names: dict[str, str] = {}

    def _get_hostgroup_names(self) -> dict[str, str]:
        if not self._hostgroup_names:
            self._hostgroup_names = {
                g["groupid"]: g["name"]
                for g in self._api.hostgroup.get(output=["groupid", "name"])
            }
        return self._hostgroup_names

    def _get_templategroup_names(self) -> dict[str, str]:
        if not self._templategroup_names:
            self._templategroup_names = {
                g["groupid"]: g["name"]
                for g in self._api.templategroup.get(output=["groupid", "name"])
            }
        return self._templategroup_names

    def _get_role_names(self) -> dict[str, str]:
        if not self._role_names:
            self._role_names = {
                r["roleid"]: r["name"]
                for r in self._api.role.get(output=["roleid", "name"])
            }
        return self._role_names

    def _get_mediatype_names(self) -> dict[str, str]:
        if not self._mediatype_names:
            self._mediatype_names = {
                m["mediatypeid"]: m["name"]
                for m in self._api.mediatype.get(output=["mediatypeid", "name"])
            }
        return self._mediatype_names

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