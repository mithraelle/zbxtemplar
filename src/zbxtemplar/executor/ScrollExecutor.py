import os

import yaml

from zbxtemplar.decree import MacroType
from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
from zbxtemplar.executor.Executor import Executor, _preflight_env_check
from zbxtemplar.executor.exceptions import ExecutorApiError, ExecutorParseError
from zabbix_utils import APIRequestError


class ScrollExecutor(Executor):

    def set_super_admin(self, data):
        data = self._resolve(data)
        password = data if isinstance(data, str) else data["password"]
        print("Updating super admin password...")
        try:
            self._api.user.update(userid="1", passwd=password)
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to update super admin password: {e}") from e

    def _validate_macro(self, macro, index=None):
        prefix = f"macro[{index}]" if index is not None else "macro"
        if not isinstance(macro, dict):
            raise ValueError(f"{prefix}: expected a mapping with 'name' and 'value', got {type(macro).__name__}")
        for key in ("name", "value"):
            if key not in macro:
                raise ValueError(f"{prefix}: missing required field '{key}'")
        macro_type = macro.get("type", MacroType.TEXT)
        if macro_type not in MacroType._API_VALUES:
            raise ValueError(f"{prefix}: invalid type '{macro_type}', expected one of: {', '.join(MacroType._API_VALUES)}")

    def _load_macros_from_file(self, path):
        data = self._load_yaml(path)
        if isinstance(data, dict) and "set_macro" in data:
            data = data["set_macro"]
        return data if isinstance(data, list) else [data]

    def set_macro(self, data):
        if isinstance(data, str):
            data = self._load_macros_from_file(data)
        if isinstance(data, list):
            flat = []
            for item in data:
                if isinstance(item, str):
                    flat.extend(self._load_macros_from_file(item))
                else:
                    flat.append(item)
            data = flat
        data = self._resolve(data)
        macros = data if isinstance(data, list) else [data]

        for i, macro in enumerate(macros):
            self._validate_macro(macro, i if len(macros) > 1 else None)

        existing = {
            m["macro"]: m["globalmacroid"]
            for m in self._api.usermacro.get(globalmacro=True)
        }

        for macro in macros:
            wire_name = "{$" + macro["name"] + "}"
            value = macro["value"]
            macro_type = MacroType._API_VALUES[macro.get("type", MacroType.TEXT)]

            if wire_name in existing:
                print(f"Updating macro {wire_name}...")
                try:
                    self._api.usermacro.updateglobal(
                        globalmacroid=existing[wire_name], value=value, type=macro_type
                    )
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update macro '{wire_name}': {e}") from e
            else:
                print(f"Creating macro {wire_name}...")
                try:
                    self._api.usermacro.createglobal(
                        macro=wire_name, value=value, type=macro_type
                    )
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create macro '{wire_name}': {e}") from e

    _IMPORT_RULES = {
        "template_groups": {"createMissing": True, "updateExisting": True},
        "templates": {"createMissing": True, "updateExisting": True},
        "host_groups": {"createMissing": True, "updateExisting": True},
        "hosts": {"createMissing": True, "updateExisting": True},
        "valueMaps": {"createMissing": True, "updateExisting": True},
        "items": {"createMissing": True, "updateExisting": True},
        "triggers": {"createMissing": True, "updateExisting": True},
        "graphs": {"createMissing": True, "updateExisting": True},
        "templateDashboards": {"createMissing": True, "updateExisting": True},
        "mediaTypes": {"createMissing": True, "updateExisting": True},
        "templateLinkage": {"createMissing": True, "deleteMissing": True},
    }

    def _apply_file(self, path):
        resolved_path = self._resolve_path(path)
        with open(resolved_path) as f:
            yaml_content = f.read()
        print(f"Importing {path}...")
        try:
            self._api.configuration.import_(
                source=yaml_content, format="yaml", rules=self._IMPORT_RULES
            )
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to import '{path}': {e}") from e

    def apply(self, data):
        if isinstance(data, list):
            for item in data:
                self._apply_file(item)
        else:
            self._apply_file(data)

    def decree(self, data):
        DecreeExecutor(self._api, base_dir=self._base_dir).decree(data)

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
            _preflight_env_check(combined)

    def run_scroll(self, scroll_path, from_stage=None, only_stage=None):
        self._base_dir = os.path.dirname(os.path.abspath(scroll_path))
        scroll = self._load_yaml(scroll_path)

        unknown = set(scroll.keys()) - {"stages"}
        if unknown:
            raise ExecutorParseError(f"Unknown keys in scroll document '{scroll_path}': {', '.join(sorted(unknown))}")

        stages = {s["stage"]: s for s in scroll["stages"]}
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