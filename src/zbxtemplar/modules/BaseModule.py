from zbxtemplar.modules import Context
from zbxtemplar.zabbix.macro import WithMacros


class BaseModule(WithMacros):
    context: Context | None = None

    def __init__(self):
        super().__init__()
        WithMacros._lookup = self.macros

    def export_macros(self) -> dict:
        if not self.macros:
            return {}
        return {"set_macro": self.macros_to_list()}
