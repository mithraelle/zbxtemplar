from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.EncryptionExecutor import EncryptionExecutor
from zbxtemplar.executor.UserGroupExecutor import UserGroupExecutor
from zbxtemplar.executor.UserExecutor import UserExecutor
from zbxtemplar.executor.ActionExecutor import ActionExecutor
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
        UserGroupExecutor(self._api).execute(data)

    def _decree_add_user(self, data):
        data = self._resolve_env(data)
        UserExecutor(self._api, self._resolve_path).execute(data)

    def _decree_actions(self, data):
        ActionExecutor(self._api).execute(data)

    def _decree_encryption(self, data):
        data = self._resolve_env(data)
        EncryptionExecutor(self._api).decree(data)

    _DECREE_ACTIONS = (
        ("user_group", "_decree_user_group"),
        ("add_user", "_decree_add_user"),
        ("actions", "_decree_actions"),
        ("encryption", "_decree_encryption"),
    )

    def decree(self, data):
        if isinstance(data, str):
            data = self._load_yaml(data)
        if isinstance(data, list):
            data = self._merge_decree(data)

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