import time

from zbxtemplar.dicts.Scroll import Scroll
from zbxtemplar.executor.DecreeExecutor import DecreeExecutor
from zbxtemplar.executor.Executor import StagedExecutor, ExecutorStage
from zbxtemplar.executor.operations.ImportOperation import ImportOperation
from zbxtemplar.executor.operations.MacroOperation import MacroOperation
from zbxtemplar.executor.operations.SuperAdminOperation import SuperAdminOperation


class ScrollExecutor(StagedExecutor):
    _ACTIONS = [
        ExecutorStage("set_super_admin", SuperAdminOperation),
        ExecutorStage("set_macro", MacroOperation),
        ExecutorStage("apply", ImportOperation),
        ExecutorStage("decree", DecreeExecutor),
    ]

    def __init__(self, spec: Scroll, api, base_dir=None):
        super().__init__(spec, api, base_dir)