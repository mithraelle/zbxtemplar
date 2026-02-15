from enum import Enum
from typing import Optional

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