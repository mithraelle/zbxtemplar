from zbxtemplar.executor.exceptions import ExecutorApiError
from zabbix_utils import APIRequestError


class ActionExecutor:
    # Condition types that store names needing ID resolution
    _CONDITION_RESOLVERS = {
        0: ("hostgroup", "groupid", "Host group"),
        1: ("host", "hostid", "Host"),
        2: ("trigger", "triggerid", "Trigger"),
        13: ("template", "templateid", "Template"),
        18: ("drule", "druleid", "Discovery rule"),
        20: ("proxy", "proxyid", "Proxy"),
    }

    def __init__(self, api):
        self._api = api

    def _resolve_conditions(self, conditions):
        lookups = {}
        for cond in conditions:
            ct = cond["conditiontype"]
            if ct in self._CONDITION_RESOLVERS and ct not in lookups:
                api_name, id_field, _ = self._CONDITION_RESOLVERS[ct]
                api = getattr(self._api, api_name)
                lookups[ct] = {
                    item["name"]: item[id_field]
                    for item in api.get(output=[id_field, "name"])
                }

        for cond in conditions:
            ct = cond["conditiontype"]
            if ct in lookups:
                _, _, label = self._CONDITION_RESOLVERS[ct]
                name = cond["value"]
                if name not in lookups[ct]:
                    raise ValueError(f"{label} '{name}' not found in Zabbix")
                cond["value"] = lookups[ct][name]

    def _resolve_operations(self, ops, ugroups, users, media_types, host_groups, templates):
        for op in ops:
            if "opmessage_grp" in op:
                for entry in op["opmessage_grp"]:
                    name = entry["usrgrpid"]
                    if name not in ugroups:
                        raise ValueError(f"User group '{name}' not found in Zabbix")
                    entry["usrgrpid"] = ugroups[name]
            if "opmessage_usr" in op:
                for entry in op["opmessage_usr"]:
                    name = entry["userid"]
                    if name not in users:
                        raise ValueError(f"User '{name}' not found in Zabbix")
                    entry["userid"] = users[name]
            if "opmessage" in op:
                msg = op["opmessage"]
                if "mediatypeid" in msg:
                    name = msg["mediatypeid"]
                    if name not in media_types:
                        raise ValueError(f"Media type '{name}' not found in Zabbix")
                    msg["mediatypeid"] = media_types[name]
            if "opgroup" in op:
                for entry in op["opgroup"]:
                    name = entry["groupid"]
                    if name not in host_groups:
                        raise ValueError(f"Host group '{name}' not found in Zabbix")
                    entry["groupid"] = host_groups[name]
            if "optemplate" in op:
                for entry in op["optemplate"]:
                    name = entry["templateid"]
                    if name not in templates:
                        raise ValueError(f"Template '{name}' not found in Zabbix")
                    entry["templateid"] = templates[name]

    def execute(self, data):
        ugroups = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}
        users = {u["username"]: u["userid"] for u in self._api.user.get(output=["userid", "username"])}
        media_types = {m["name"]: m["mediatypeid"] for m in self._api.mediatype.get(output=["mediatypeid", "name"])}
        host_groups = {g["name"]: g["groupid"] for g in self._api.hostgroup.get(output=["groupid", "name"])}
        templates = {t["name"]: t["templateid"] for t in self._api.template.get(output=["templateid", "name"])}
        existing = {a["name"]: a["actionid"] for a in self._api.action.get(output=["actionid", "name"])}

        for action in data:
            name = action["name"]

            if "filter" in action and "conditions" in action["filter"]:
                self._resolve_conditions(action["filter"]["conditions"])

            for op_key in ("operations", "recovery_operations", "update_operations"):
                if op_key in action:
                    self._resolve_operations(action[op_key], ugroups, users, media_types, host_groups, templates)

            if name in existing:
                action["actionid"] = existing[name]
                del action["name"]
                print(f"Updating action '{name}'...")
                try:
                    self._api.action.update(**action)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update action '{name}': {e}") from e
            else:
                print(f"Creating action '{name}'...")
                try:
                    self._api.action.create(**action)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create action '{name}': {e}") from e