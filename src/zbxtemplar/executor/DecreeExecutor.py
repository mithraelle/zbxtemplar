from zbxtemplar.DictEntity import SchemaField
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.operations.EncryptionOperation import EncryptionOperation
from zbxtemplar.executor.operations.UserGroupOperation import UserGroupOperation
from zbxtemplar.executor.operations.UserOperation import UserOperation
from zbxtemplar.executor.operations.ActionOperation import ActionOperation


class DecreeExecutor(Executor):

    _DECREE_ACTIONS = (
        ("user_group", UserGroupOperation),
        ("add_user", UserOperation),
        ("actions", ActionOperation),
        ("encryption", EncryptionOperation),
    )

    _SCHEMA = [SchemaField(key) for key, _ in _DECREE_ACTIONS]

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