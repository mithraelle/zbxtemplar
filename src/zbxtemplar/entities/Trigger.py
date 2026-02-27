from enum import Enum
from typing import List, Optional

from zbxtemplar.core.ZbxEntity import ZbxEntity, WithTags


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