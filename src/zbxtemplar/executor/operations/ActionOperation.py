from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log
from zabbix_utils import APIRequestError
from zbxtemplar.decree.Action import (
    Action, CONDITION_RESOLVERS, OP_LIST_TARGETS, OP_DICT_TARGETS,
)


class ActionOperation(Executor):
    def __init__(self, spec: list[Action], api, base_dir=None):
        super().__init__(spec, api, base_dir)
        self._lookups: dict[tuple, dict[str, str]] = {}

    def _name_id_map(self, api_name: str, id_field: str, name_field: str = "name") -> dict[str, str]:
        key = (api_name, id_field, name_field)
        if key not in self._lookups:
            items = getattr(self._api, api_name).get(output=[id_field, name_field])
            self._lookups[key] = {item[name_field]: item[id_field] for item in items}
        return self._lookups[key]

    def _resolve_conditions(self, conditions):
        for cond in conditions:
            ct = cond["conditiontype"]
            if ct not in CONDITION_RESOLVERS:
                continue
            api_name, id_field, label = CONDITION_RESOLVERS[ct]
            lookup = self._name_id_map(api_name, id_field)
            name = cond["value"]
            if name not in lookup:
                raise ValueError(f"{label} '{name}' not found in Zabbix")
            cond["value"] = lookup[name]

    def _resolve_operations(self, ops):
        for op in ops:
            for parent, id_field, api_name, name_field, label in OP_LIST_TARGETS:
                if parent not in op:
                    continue
                lookup = self._name_id_map(api_name, id_field, name_field)
                for entry in op[parent]:
                    name = entry[id_field]
                    if name not in lookup:
                        raise ValueError(f"{label} '{name}' not found in Zabbix")
                    entry[id_field] = lookup[name]
            for parent, id_field, api_name, name_field, label in OP_DICT_TARGETS:
                if parent not in op or id_field not in op[parent]:
                    continue
                lookup = self._name_id_map(api_name, id_field, name_field)
                name = op[parent][id_field]
                if name not in lookup:
                    raise ValueError(f"{label} '{name}' not found in Zabbix")
                op[parent][id_field] = lookup[name]

    def _validate(self):
        pass

    def execute(self):
        existing = {a["name"]: a["actionid"] for a in self._api.action.get(output=["actionid", "name"])}
        log.lookup_end("actions", count=len(existing))

        for action_obj in self._spec:
            action = action_obj.to_dict()
            name = action["name"]

            if "filter" in action and "conditions" in action["filter"]:
                self._resolve_conditions(action["filter"]["conditions"])

            for op_key in ("operations", "recovery_operations", "update_operations"):
                if op_key in action:
                    self._resolve_operations(action[op_key])

            if name in existing:
                action["actionid"] = existing[name]
                del action["name"]
                try:
                    self._api.action.update(**action)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update action '{name}': {e}") from e
                log.entity_end("action", action="update", name=name, id=existing[name])
            else:
                try:
                    result = self._api.action.create(**action)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create action '{name}': {e}") from e
                actionid = (result or {}).get("actionids", [None])[0]
                log.entity_end("action", action="create", name=name, id=actionid)