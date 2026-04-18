import hashlib
import os
import re
import time
from dataclasses import dataclass
from typing import ClassVar, Mapping

import yaml

from zbxtemplar.executor.exceptions import ExecutorParseError
from zbxtemplar.executor.log import log

class Executor:
    def __init__(self, spec, api, base_dir=None):
        self._api = api
        self._base_dir = base_dir
        self._spec = spec
        self._validate()

    def action_info(self):
        if isinstance(self._spec, list):
            return {"items": len(self._spec)}
        return {}

    def execute(self):
        raise NotImplementedError()

    def _validate(self):
        raise NotImplementedError()

    def _resolve_path(self, path):
        if self._base_dir and not os.path.isabs(path):
            return os.path.join(self._base_dir, path)
        return path


@dataclass
class ExecutorStage:
    action: str
    executor: type[Executor]


class StagedExecutor(Executor):
    _ACTIONS: ClassVar[list[ExecutorStage]] = []

    def __init__(self, spec, api, base_dir=None):
        if not self._ACTIONS:
            raise RuntimeError(f"{type(self).__name__} has no executor stages configured")
        self._ops: list[tuple[str, Executor]] = []
        super().__init__(spec, api, base_dir)

    def _stage_spec(self, action):
        if isinstance(self._spec, Mapping):
            return self._spec.get(action)
        return getattr(self._spec, action, None)

    def _validate(self):
        for stage in self._ACTIONS:
            spec = self._stage_spec(stage.action)
            if spec is None:
                continue
            self._ops.append(
                (stage.action, stage.executor(spec, self._api, self._base_dir))
            )

    def execute(self, from_action=None, only_action=None):
        valid = [s.action for s in self._ACTIONS]
        val = from_action or only_action
        if val and val not in valid:
            raise ValueError(f"Unknown action: {val}. Valid: {', '.join(valid)}")

        ops = self._ops
        if only_action:
            ops = [(k, o) for k, o in ops if k == only_action]
        elif from_action:
            start = next((i for i, (k, _) in enumerate(ops) if k == from_action), None)
            if start is not None:
                ops = ops[start:]

        for key, op in ops:
            t0 = time.time()
            log.action_start(key, **op.action_info())
            op.execute()
            log.action_end(key, result="ok", duration_ms=int((time.time() - t0) * 1000))
