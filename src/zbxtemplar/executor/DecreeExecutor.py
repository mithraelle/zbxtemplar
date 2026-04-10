from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.operations.EncryptionOperation import EncryptionOperation
from zbxtemplar.executor.operations.UserGroupOperation import UserGroupOperation
from zbxtemplar.executor.operations.UserOperation import UserOperation
from zbxtemplar.executor.operations.ActionOperation import ActionOperation
from zbxtemplar.executor.exceptions import ExecutorParseError


class DecreeExecutor(Executor):

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

    def _decree_user_group(self, data):
        UserGroupOperation(self._api, self._base_dir).execute(data)

    def _decree_add_user(self, data):
        UserOperation(self._api, self._base_dir).execute(data)

    def _decree_actions(self, data):
        ActionOperation(self._api, self._base_dir).execute(data)

    def _decree_encryption(self, data):
        EncryptionOperation(self._api, self._base_dir).execute(data)

    _DECREE_ACTIONS = (
        ("user_group", "_decree_user_group"),
        ("add_user", "_decree_add_user"),
        ("actions", "_decree_actions"),
        ("encryption", "_decree_encryption"),
    )

    def execute(self, data):
        if isinstance(data, str):
            data = self._load_yaml(data)
        if isinstance(data, list):
            data = self._merge_decree(data)

        data = self._resolve_env(data)

        unknown = set(data.keys()) - {k for k, _ in self._DECREE_ACTIONS}
        if unknown:
            raise ExecutorParseError(f"Unknown keys in decree document: {', '.join(sorted(unknown))}")

        for key, method in self._DECREE_ACTIONS:
            if key in data:
                getattr(self, method)(data[key])

    def add_user(self, data):
        if isinstance(data, str):
            data = self._load_yaml(data)
        if isinstance(data, dict):
            if "add_user" in data:
                data = data["add_user"]
            else:
                data = [data]
        self._decree_add_user(data)