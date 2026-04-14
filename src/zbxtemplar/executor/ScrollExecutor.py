import time

from zbxtemplar.dicts.Scroll import Scroll
from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.log import log
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

    def from_data(self, data):
        Scroll.validate(data)
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
            t0 = time.time()
            log.action_start(key, **op.action_info())
            op.execute()
            log.action_end(key, result="ok", duration_ms=int((time.time() - t0) * 1000))
