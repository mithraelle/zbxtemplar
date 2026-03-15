from enum import Enum
from typing import List, Optional

from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, WithTags


class TriggerPriority(str, Enum):
    NOT_CLASSIFIED = "NOT_CLASSIFIED"
    INFO = "INFO"
    WARNING = "WARNING"
    AVERAGE = "AVERAGE"
    HIGH = "HIGH"
    DISASTER = "DISASTER"


class Trigger(ZbxEntity, WithTags):
    def __init__(self, name: str, expression: str,
                 priority: TriggerPriority = TriggerPriority.NOT_CLASSIFIED,
                 description: Optional[str] = None):
        super().__init__(name)
        self.expression = expression
        self.priority = priority
        self.description = description

    @classmethod
    def from_dict(cls, data: dict):
        trigger = cls(
            name=data["name"],
            expression=data.get("expression", ""),
            priority=TriggerPriority(data.get("priority", "NOT_CLASSIFIED")),
            description=data.get("description"),
        )
        for t in data.get("tags", []):
            trigger.add_tag(t["tag"], t.get("value", ""))
        return trigger


class WithTriggers:
    def __init__(self):
        super().__init__()
        self._triggers: List[Trigger] = []

    def add_trigger(self, name: str, expression: str,
                    priority: TriggerPriority = TriggerPriority.NOT_CLASSIFIED,
                    description: Optional[str] = None):
        if not any(t.name == name for t in self._triggers):
            self._triggers.append(Trigger(name, expression, priority, description))
        return self

    @property
    def triggers(self):
        return list(self._triggers)