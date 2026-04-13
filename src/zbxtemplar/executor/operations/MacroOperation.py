from zabbix_utils import APIRequestError

from zbxtemplar.zabbix.ZbxEntity import Macro, MacroType
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log


class MacroOperation(Executor):
    _OMIT_FROM_SCHEMA_DOCS = True

    def _load_macros_from_file(self, path):
        data = self._load_yaml(path)
        if isinstance(data, dict) and "set_macro" in data:
            data = data["set_macro"]
        return data if isinstance(data, list) else [data]

    def from_data(self, data):
        raw = data if isinstance(data, list) else [data]
        flat = []
        for item in raw:
            if isinstance(item, str):
                flat.extend(self._load_macros_from_file(item))
            else:
                flat.append(item)
        self._macros = [Macro.from_dict(m) for m in flat]

    def action_info(self):
        return {"items": len(self._macros)}

    def execute(self):
        existing = {
            m["macro"]: m["globalmacroid"]
            for m in self._api.usermacro.get(globalmacro=True)
        }
        log.lookup_end("global_macros", count=len(existing))

        for macro in self._macros:
            if macro.full_name in existing:
                try:
                    self._api.usermacro.updateglobal(
                        globalmacroid=existing[macro.full_name],
                        value=macro.value,
                        type=MacroType._API_VALUES[macro.type],
                    )
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update macro '{macro.full_name}': {e}") from e
                log.entity_end("macro", action="update", name=macro.full_name, value_redacted=True)
            else:
                try:
                    self._api.usermacro.createglobal(
                        macro=macro.full_name,
                        value=macro.value,
                        type=MacroType._API_VALUES[macro.type],
                    )
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create macro '{macro.full_name}': {e}") from e
                extra = {"value_redacted": True}
                if macro.type != MacroType.TEXT:
                    extra["secret_type"] = str(macro.type)
                log.entity_end("macro", action="create", name=macro.full_name, **extra)