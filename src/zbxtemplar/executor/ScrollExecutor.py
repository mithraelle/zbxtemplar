import os

from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.operations.ImportOperation import ImportOperation
from zbxtemplar.executor.operations.MacroOperation import MacroOperation
from zbxtemplar.executor.exceptions import ExecutorApiError, ExecutorParseError
from zabbix_utils import APIRequestError


class ScrollExecutor(Executor):

    def set_super_admin(self, data):
        data = self._resolve_env(data)
        password = data if isinstance(data, str) else data["password"]
        print("Updating super admin password...")
        try:
            self._api.user.update(userid="1", passwd=password)
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to update super admin password: {e}") from e

    def set_macro(self, data):
        MacroOperation(self._api, self._base_dir).execute(data)

    def apply(self, data):
        ImportOperation(self._api, self._base_dir).execute(data)

    def decree(self, data):
        DecreeExecutor(self._api, base_dir=self._base_dir).execute(data)

    PIPELINE = (
        ("bootstrap", ("set_super_admin", "set_macro")),
        ("templates", ("apply",)),
        ("state",     ("decree",)),
    )

    def _preflight_scroll(self, stages):
        combined = []
        for stage in stages.values():
            for action_name in ("set_macro", "decree"):
                value = stage.get(action_name)
                if value is None:
                    continue
                if isinstance(value, str):
                    combined.append(self._load_yaml(value))
                elif isinstance(value, dict):
                    combined.append(value)
                elif isinstance(value, list):
                    for entry in value:
                        if isinstance(entry, str):
                            combined.append(self._load_yaml(entry))
                        else:
                            combined.append(entry)
        if combined:
            self._resolve_env(combined)

    def run_scroll(self, scroll_path, from_stage=None, only_stage=None):
        self._base_dir = os.path.dirname(os.path.abspath(scroll_path))
        scroll = self._load_yaml(scroll_path)

        known = {name for name, _ in self.PIPELINE}
        unknown = set(scroll.keys()) - known
        if unknown:
            raise ExecutorParseError(f"Unknown keys in scroll document '{scroll_path}': {', '.join(sorted(unknown))}")

        stages = scroll
        self._preflight_scroll(stages)

        pipeline = self.PIPELINE
        if only_stage:
            pipeline = [(name, actions) for name, actions in pipeline if name == only_stage]
        elif from_stage:
            start = next((i for i, (name, _) in enumerate(pipeline) if name == from_stage), None)
            if start is not None:
                pipeline = pipeline[start:]

        for stage_name, actions in pipeline:
            if stage_name not in stages:
                continue
            stage = stages[stage_name]
            print(f"--- stage: {stage_name}")
            for action in actions:
                if action in stage:
                    getattr(self, action)(stage[action])