from enum import StrEnum

from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, WithTags


class TriggerPriority(StrEnum):
    """Trigger severity level."""

    NOT_CLASSIFIED = "NOT_CLASSIFIED"
    INFO = "INFO"
    WARNING = "WARNING"
    AVERAGE = "AVERAGE"
    HIGH = "HIGH"
    DISASTER = "DISASTER"


class Trigger(ZbxEntity, WithTags):
    def __init__(self, name: str, expression: str,
                 priority: TriggerPriority = TriggerPriority.NOT_CLASSIFIED,
                 description: str | None = None):
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
        self._triggers: list[Trigger] = []

    def add_trigger(self, name: str, expression: str,
                    priority: TriggerPriority = TriggerPriority.NOT_CLASSIFIED,
                    description: str | None = None):
        """Attach a trigger with a full expression string. Raises on duplicate name.

        Use this for multi-item expressions built with ``Item.expr()``.
        Use ``Item.add_trigger()`` instead when the trigger belongs to a single item.

        Args:
            expression: Complete Zabbix trigger expression, e.g. ``last(/host/key)>5``.
            priority: TriggerPriority constant; defaults to NOT_CLASSIFIED.
        """
        if any(t.name == name for t in self._triggers):
            raise ValueError(
                f"Duplicate trigger '{name}' on '{getattr(self, 'name', type(self).__name__)}'"
            )
        self._triggers.append(Trigger(name, expression, priority, description))
        return self

    @property
    def triggers(self):
        return list(self._triggers)