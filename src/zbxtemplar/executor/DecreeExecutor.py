from zbxtemplar.dicts.Decree import Decree
from zbxtemplar.executor.Executor import StagedExecutor, ExecutorStage
from zbxtemplar.executor.operations.EncryptionOperation import EncryptionOperation
from zbxtemplar.executor.operations.UserGroupOperation import UserGroupOperation
from zbxtemplar.executor.operations.UserOperation import UserOperation
from zbxtemplar.executor.operations.ActionOperation import ActionOperation


class DecreeExecutor(StagedExecutor):
    _ACTIONS = [
        ExecutorStage("user_group", UserGroupOperation),
        ExecutorStage("add_user", UserOperation),
        ExecutorStage("actions", ActionOperation),
        ExecutorStage("encryption", EncryptionOperation),
    ]

    def __init__(self, spec: Decree, api, base_dir=None):
        super().__init__(spec, api, base_dir)