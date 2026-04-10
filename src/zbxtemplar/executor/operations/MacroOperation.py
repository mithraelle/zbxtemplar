from zabbix_utils import APIRequestError

from zbxtemplar.decree import MacroType
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError


class MacroOperation(Executor):

    def _validate_macro(self, macro, index=None):
        prefix = f"macro[{index}]" if index is not None else "macro"
        if not isinstance(macro, dict):
            raise ValueError(f"{prefix}: expected a mapping with 'name' and 'value', got {type(macro).__name__}")
        for key in ("name", "value"):
            if key not in macro:
                raise ValueError(f"{prefix}: missing required field '{key}'")
        macro_type = macro.get("type", MacroType.TEXT)
        if macro_type not in MacroType._API_VALUES:
            raise ValueError(f"{prefix}: invalid type '{macro_type}', expected one of: {', '.join(MacroType._API_VALUES)}")

    def _load_macros_from_file(self, path):
        data = self._load_yaml(path)
        if isinstance(data, dict) and "set_macro" in data:
            data = data["set_macro"]
        return data if isinstance(data, list) else [data]

    def execute(self, data):
        if isinstance(data, str):
            data = self._load_macros_from_file(data)
        if isinstance(data, list):
            flat = []
            for item in data:
                if isinstance(item, str):
                    flat.extend(self._load_macros_from_file(item))
                else:
                    flat.append(item)
            data = flat
        data = self._resolve_env(data)
        macros = data if isinstance(data, list) else [data]

        for i, macro in enumerate(macros):
            self._validate_macro(macro, i if len(macros) > 1 else None)

        existing = {
            m["macro"]: m["globalmacroid"]
            for m in self._api.usermacro.get(globalmacro=True)
        }

        for macro in macros:
            wire_name = "{$" + macro["name"] + "}"
            value = macro["value"]
            macro_type = MacroType._API_VALUES[macro.get("type", MacroType.TEXT)]

            if wire_name in existing:
                print(f"Updating macro {wire_name}...")
                try:
                    self._api.usermacro.updateglobal(
                        globalmacroid=existing[wire_name], value=value, type=macro_type
                    )
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update macro '{wire_name}': {e}") from e
            else:
                print(f"Creating macro {wire_name}...")
                try:
                    self._api.usermacro.createglobal(
                        macro=wire_name, value=value, type=macro_type
                    )
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create macro '{wire_name}': {e}") from e