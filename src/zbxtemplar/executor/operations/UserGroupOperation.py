from zbxtemplar.decree import UserGroup, GuiAccess, Permission, UsersStatus
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log
from zabbix_utils import APIRequestError


class UserGroupOperation(Executor):
    def __init__(self, spec: list[UserGroup], api, base_dir=None):
        super().__init__(spec, api, base_dir)

    def _resolve_rights(self, groups, group_lookup, label):
        rights = []
        for g in groups:
            name = g["name"]
            if name not in group_lookup:
                raise ValueError(f"{label} '{name}' not found in Zabbix")
            perm = g.get("permission", Permission.READ)
            rights.append({"id": group_lookup[name], "permission": Permission(perm).api})
        return rights

    def _validate(self):
        pass

    def execute(self):
        host_groups = {g["name"]: g["groupid"] for g in self._api.hostgroup.get(output=["groupid", "name"])}
        template_groups = {g["name"]: g["groupid"] for g in self._api.templategroup.get(output=["groupid", "name"])}
        existing = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}
        log.lookup_end("user_groups", count=len(existing))

        for ug in self._spec:
            gui = ug.gui_access or GuiAccess.DEFAULT
            params = {"name": ug.name, "gui_access": GuiAccess(gui).api}

            if ug.users_status is not None:
                params["users_status"] = UsersStatus(ug.users_status).api

            if ug.host_groups:
                params["hostgroup_rights"] = self._resolve_rights(ug.host_groups, host_groups, "Host group")
            if ug.template_groups:
                params["templategroup_rights"] = self._resolve_rights(ug.template_groups, template_groups, "Template group")

            if ug.name in existing:
                params["usrgrpid"] = existing[ug.name]
                del params["name"]
                try:
                    self._api.usergroup.update(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update user group '{ug.name}': {e}") from e
                log.entity_end("user_group", action="update", name=ug.name, id=existing[ug.name])
            else:
                try:
                    result = self._api.usergroup.create(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create user group '{ug.name}': {e}") from e
                usrgrpid = (result or {}).get("usrgrpids", [None])[0]
                log.entity_end("user_group", action="create", name=ug.name, id=usrgrpid)
