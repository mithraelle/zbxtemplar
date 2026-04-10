from zbxtemplar.decree import UserGroup, GuiAccess, Permission
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zabbix_utils import APIRequestError


class UserGroupOperation(Executor):
    def _resolve_rights(self, groups, group_lookup, label):
        rights = []
        for g in groups:
            name = g["name"]
            if name not in group_lookup:
                raise ValueError(f"{label} '{name}' not found in Zabbix")
            perm = g.get("permission", Permission.READ)
            rights.append({"id": group_lookup[name], "permission": Permission._API_VALUES[perm]})
        return rights

    def execute(self, data):
        host_groups = {g["name"]: g["groupid"] for g in self._api.hostgroup.get(output=["groupid", "name"])}
        template_groups = {g["name"]: g["groupid"] for g in self._api.templategroup.get(output=["groupid", "name"])}
        existing = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}

        for raw in data:
            ug = UserGroup.from_dict(raw)
            gui = ug.gui_access or GuiAccess.DEFAULT
            params = {"name": ug.name, "gui_access": GuiAccess._API_VALUES[gui]}

            if ug.host_groups:
                params["hostgroup_rights"] = self._resolve_rights(ug.host_groups, host_groups, "Host group")
            if ug.template_groups:
                params["templategroup_rights"] = self._resolve_rights(ug.template_groups, template_groups, "Template group")

            if ug.name in existing:
                params["usrgrpid"] = existing[ug.name]
                del params["name"]
                print(f"Updating user group '{ug.name}'...")
                try:
                    self._api.usergroup.update(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update user group '{ug.name}': {e}") from e
            else:
                print(f"Creating user group '{ug.name}'...")
                try:
                    self._api.usergroup.create(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create user group '{ug.name}': {e}") from e