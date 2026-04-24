from zbxtemplar.modules.Context import Context
from zbxtemplar.zabbix.macro import WithMacros


class BaseModule(WithMacros):
    context: Context | None = None

    def __init__(self, **kwargs):
        super().__init__()
        WithMacros._lookup = self.macros
        self.compose(**kwargs)

    def compose(self, **kwargs):
        raise NotImplementedError(f"{type(self).__name__} must implement compose()")

    def export_macros(self) -> dict:
        if not self.macros:
            return {}
        return {"set_macro": self.macros_to_list()}
