import os
import re

import yaml

from zbxtemplar.executor.exceptions import ExecutorParseError


def _resolve_env(value):
    if not isinstance(value, str):
        return value

    def replace(match):
        var = match.group(1)
        env_val = os.environ.get(var)
        if env_val is None:
            raise ValueError(f"Environment variable '{var}' is not set")
        return env_val

    return re.sub(r'\$\{(\w+)\}', replace, value)


def _resolve_deep(obj):
    if isinstance(obj, str):
        return _resolve_env(obj)
    if isinstance(obj, dict):
        return {k: _resolve_deep(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_deep(v) for v in obj]
    return obj


def _preflight_env_check(obj):
    missing = set()

    def scan(obj):
        if isinstance(obj, str):
            for match in re.finditer(r'\$\{(\w+)\}', obj):
                var = match.group(1)
                if os.environ.get(var) is None:
                    missing.add(var)
        elif isinstance(obj, dict):
            for v in obj.values():
                scan(v)
        elif isinstance(obj, list):
            for v in obj:
                scan(v)

    scan(obj)
    if missing:
        lines = "\n".join(f"  {var}" for var in sorted(missing))
        raise ValueError(
            f"Pre-flight check failed. Missing environment variables:\n{lines}\n\n"
            "Execution aborted. No changes were made."
        )


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
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ExecutorParseError(f"Failed to parse '{resolved_path}': {e}", path=resolved_path) from e

    def _resolve(self, data):
        _preflight_env_check(data)
        return _resolve_deep(data)