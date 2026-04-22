from enum import StrEnum

from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, WithTags
from zbxtemplar.zabbix.trigger_expression import TriggerExpr


class TriggerPriority(StrEnum):
    """Trigger severity level."""

    NOT_CLASSIFIED = "NOT_CLASSIFIED"
    INFO = "INFO"
    WARNING = "WARNING"
    AVERAGE = "AVERAGE"
    HIGH = "HIGH"
    DISASTER = "DISASTER"


class Trigger(ZbxEntity, WithTags):
    def __init__(self, name: str, expression: TriggerExpr,
                 priority: TriggerPriority = TriggerPriority.NOT_CLASSIFIED,
                 description: str | None = None):
        super().__init__(name)
        s = str(expression)
        self.expression = s[1:-1] if s.startswith("(") and s.endswith(")") else s
        self.priority = priority
        self.description = description

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls.__new__(cls)
        ZbxEntity.__init__(obj, data["name"])
        WithTags.__init__(obj)
        obj.expression = data.get("expression", "")
        obj.priority = TriggerPriority(data.get("priority", "NOT_CLASSIFIED"))
        obj.description = data.get("description")
        for t in data.get("tags", []):
            obj.add_tag(t["tag"], t.get("value", ""))
        return obj


class WithTriggers:
    def __init__(self):
        super().__init__()
        self._triggers: list[Trigger] = []

    def add_trigger(self, name: str, expression: TriggerExpr,
                    priority: TriggerPriority = TriggerPriority.NOT_CLASSIFIED,
                    description: str | None = None):
        """Attach a trigger. Raises on duplicate name.

        Single-item expressions are inlined on the referenced item (Zabbix expects
        host-item triggers under ``items[].triggers[]``); multi-item expressions
        stay on the owning entity and are emitted at the top level.
        """
        owner = getattr(self, "name", type(self).__name__)
        own_items = getattr(self, "items", [])
        existing = list(self._triggers)
        for it in own_items:
            existing.extend(it.triggers)
        if any(t.name == name for t in existing):
            raise ValueError(f"Duplicate trigger '{name}' on '{owner}'")

        trigger = Trigger(name, expression, priority, description)
        refs = expression.items()
        for item in refs:
            if not any(i is item for i in own_items):
                raise ValueError(
                    f"Trigger '{name}' references item '{item.key}' not owned by '{owner}'"
                )
        if len(refs) == 1:
            refs[0].triggers.append(trigger)
        else:
            self._triggers.append(trigger)
        return self

    @property
    def triggers(self):
        return list(self._triggers)