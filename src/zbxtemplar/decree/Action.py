from abc import ABC
from typing import Union

from zbxtemplar.core.DecreeEntity import DecreeEntity
from zbxtemplar.decree.action_conditions import ConditionList, ConditionExpression, ConditionExpr
from zbxtemplar.decree.action_operations import TriggerOperations, TriggerAckOperations


class Action(DecreeEntity, ABC):
    eventsource = None

    def __init__(self, name: str):
        self.name = name
        self._filter = None

    def set_conditions(self, conditions: Union[ConditionList, ConditionExpression, ConditionExpr]):
        if isinstance(conditions, ConditionExpr):
            conditions = ConditionExpression(conditions)
        self._filter = conditions
        return self

    def to_dict(self) -> dict:
        result = {"eventsource": self.eventsource}
        result.update(super().to_dict())
        if self._filter is not None:
            result["filter"] = self._filter.to_dict()
        return result


class TriggerAction(Action):
    eventsource = 0

    def __init__(self, name: str):
        super().__init__(name)
        self.operations = TriggerOperations()
        self.recovery_operations = TriggerAckOperations()
        self.update_operations = TriggerAckOperations()

    def set_operation_step(self, duration: int):
        self.esc_period = duration
        return self

    def pause_symptoms(self):
        self.pause_symptoms = 0
        return self

    def pause_suppressed(self):
        self.pause_suppressed = 0
        return self

    def notify_if_canceled(self):
        self.notify_if_canceled = 0
        return self

    def operations_to_list(self) -> list:
        return self.operations.to_list()

    def recovery_operations_to_list(self) -> list:
        return self.recovery_operations.to_list()

    def update_operations_to_list(self) -> list:
        return self.update_operations.to_list()