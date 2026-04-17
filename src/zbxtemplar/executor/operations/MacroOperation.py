from zabbix_utils import APIRequestError

from zbxtemplar.zabbix import MacroType
from zbxtemplar.zabbix.macro import Macro
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log


class MacroOperation(Executor):
    def __init__(self, spec: list[Macro], api, base_dir=None):
        super().__init__(spec, api, base_dir)

    def _validate(self):
        pass

    def execute(self):
        existing = {
            m["macro"]: m["globalmacroid"]
            for m in self._api.usermacro.get(globalmacro=True)
        }
        log.lookup_end("global_macros", count=len(existing))

        for macro in self._spec:
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
