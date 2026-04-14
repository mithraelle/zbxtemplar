from zbxtemplar.modules import Context
from zbxtemplar.zabbix.macro import WithMacros


class BaseModule(WithMacros):
    def __init__(self, context: Context | None = None):
        super().__init__()
        self.context = context
        WithMacros._context = context._macros if context else {}
        WithMacros._lookup = self.macros

    def export_macros(self) -> dict:
        if not self.macros:
            return {}
        return {"set_macro": self.macros_to_list()}