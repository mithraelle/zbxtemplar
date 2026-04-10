import os
import re

import yaml

from zbxtemplar.executor.exceptions import ExecutorParseError


class Executor:
    def __init__(self, api, base_dir=None):
        self._api = api
        self._base_dir = base_dir

    def _resolve_path(self, path):
        if self._base_dir and not os.path.isabs(path):
            return os.path.join(self._base_dir, path)
        return path

    def _load_yaml(self, path):
        resolved_path = self._resolve_path(path)
        try:
            with open(resolved_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ExecutorParseError(f"Failed to parse '{resolved_path}': {e}", path=resolved_path) from e
        return self._resolve_env(data)

    @staticmethod
    def _resolve_env(obj):
        missing = set()

        def replace(match):
            var = match.group(1)
            env_val = os.environ.get(var)
            if env_val is None:
                missing.add(var)
                return ""
            return env_val

        def walk(o):
            if isinstance(o, str):
                return re.sub(r'\$\{(\w+)\}', replace, o)
            if isinstance(o, dict):
                return {k: walk(v) for k, v in o.items()}
            if isinstance(o, list):
                return [walk(v) for v in o]
            return o

        result = walk(obj)
        if missing:
            lines = "\n".join(f"  {var}" for var in sorted(missing))
            raise ValueError(
                f"Pre-flight check failed. Missing environment variables:\n{lines}\n\n"
                "Execution aborted. No changes were made."
            )
        return result

    def execute(self, data):
        raise NotImplementedError