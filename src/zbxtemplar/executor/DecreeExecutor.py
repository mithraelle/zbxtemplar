from zbxtemplar.DictEntity import SchemaField
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.operations.EncryptionOperation import EncryptionOperation
from zbxtemplar.executor.operations.UserGroupOperation import UserGroupOperation
from zbxtemplar.executor.operations.UserOperation import UserOperation
from zbxtemplar.executor.operations.ActionOperation import ActionOperation


class DecreeExecutor(Executor):
    """Executor for decree YAML sections such as user groups, users, actions, and encryption."""

    _DECREE_ACTIONS = (
        ("user_group", UserGroupOperation),
        ("add_user", UserOperation),
        ("actions", ActionOperation),
        ("encryption", EncryptionOperation),
    )

    _SCHEMA = [
        SchemaField("user_group", str_type="list[UserGroup]", description="User group definitions to create or update before users."),
        SchemaField("add_user", str_type="list[User]", description="User definitions to create or update."),
        SchemaField("actions", str_type="list[dict]", description="Zabbix action definitions to create or update."),
        SchemaField("encryption", str_type="dict | list[dict]", description="Host encryption settings with host_defaults and hosts entries."),
    ]

    def _merge_decree(self, sources):
        merged = {}
        for src in sources:
            if isinstance(src, str):
                src = self._load_yaml(src)
            for key in src:
                merged.setdefault(key, []).extend(
                    src[key] if isinstance(src[key], list) else [src[key]]
                )
        return merged

    def from_data(self, data):
        if isinstance(data, str):
            data = self._load_yaml(data)
        if isinstance(data, list):
            data = self._merge_decree(data)
        super().from_data(data)
        self._ops = []
        for key, op_class in self._DECREE_ACTIONS:
            if key not in data:
                continue
            op = op_class(self._api, self._base_dir)
            op.from_data(data[key])
            self._ops.append(op)

    def execute(self):
        for op in self._ops:
            op.execute()
