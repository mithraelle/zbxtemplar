from zbxtemplar.DictEntity import SchemaField
from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.operations.ImportOperation import ImportOperation
from zbxtemplar.executor.operations.MacroOperation import MacroOperation
from zbxtemplar.executor.operations.SuperAdminOperation import SuperAdminOperation


class ScrollExecutor(Executor):
    """Executor for ordered scroll actions that combine bootstrap, import, and decree steps."""

    _SCROLL_ACTIONS = (
        ("set_super_admin", SuperAdminOperation),
        ("set_macro", MacroOperation),
        ("apply", ImportOperation),
        ("decree", DecreeExecutor),
    )

    _SCHEMA = [
        SchemaField("set_super_admin", str_type="str | dict", description="New built-in Admin password as a string or password mapping."),
        SchemaField("set_macro", str_type="str | dict | list", description="Global macro definition, list of definitions, or path to a macro YAML file."),
        SchemaField("apply", str_type="str | list[str]", description="Zabbix-native YAML file path or paths to import."),
        SchemaField("decree", str_type="dict | list | str", description="Inline decree data, merged decree data list, or decree YAML path."),
    ]

    def from_data(self, data):
        super().from_data(data)
        self._ops = []
        for key, op_class in self._SCROLL_ACTIONS:
            if key not in data:
                continue
            op = op_class(self._api, self._base_dir)
            op.from_data(data[key])
            self._ops.append((key, op))

    def execute(self, from_action=None, only_action=None):
        ops = self._ops
        if only_action:
            ops = [(k, o) for k, o in ops if k == only_action]
        elif from_action:
            start = next((i for i, (k, _) in enumerate(ops) if k == from_action), None)
            if start is not None:
                ops = ops[start:]

        for key, op in ops:
            print(f"--- {key}")
            op.execute()
