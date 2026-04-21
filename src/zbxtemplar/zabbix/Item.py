from __future__ import annotations

from enum import StrEnum
from typing import Self, TYPE_CHECKING

from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, WithTags
from zbxtemplar.zabbix.Trigger import Trigger, TriggerPriority

if TYPE_CHECKING:
    from zbxtemplar.zabbix.Template import ValueMap
    from zbxtemplar.zabbix.Host import HostInterface


class ItemType(StrEnum):
    """Item collection method (how Zabbix gathers the value)."""

    ZABBIX_PASSIVE = "ZABBIX_PASSIVE"
    TRAP = "TRAP"
    SIMPLE = "SIMPLE"
    INTERNAL = "INTERNAL"
    ZABBIX_ACTIVE = "ZABBIX_ACTIVE"
    EXTERNAL = "EXTERNAL"
    ODBC = "ODBC"
    IPMI = "IPMI"
    SSH = "SSH"
    TELNET = "TELNET"
    CALCULATED = "CALCULATED"
    JMX = "JMX"
    SNMP_TRAP = "SNMP_TRAP"
    DEPENDENT = "DEPENDENT"
    HTTP_AGENT = "HTTP_AGENT"
    SNMP_AGENT = "SNMP_AGENT"
    ITEM_TYPE_SCRIPT = "ITEM_TYPE_SCRIPT"
    ITEM_TYPE_BROWSER = "ITEM_TYPE_BROWSER"


class ValueType(StrEnum):
    """Data type of the collected item value."""

    FLOAT = "FLOAT"
    CHAR = "CHAR"
    LOG = "LOG"
    UNSIGNED = "UNSIGNED"
    TEXT = "TEXT"
    BINARY = "BINARY"


class Item(ZbxEntity, WithTags):
    """Zabbix monitoring item. UUID is derived from key, not name.

    The host is set automatically when the item is registered via
    ``Template.add_item()`` or ``Host.add_item()``.
    """

    def __init__(self, name: str, key: str, host: str = "",
                 type: ItemType = ItemType.ZABBIX_PASSIVE,
                 value_type: ValueType = ValueType.UNSIGNED,
                 history: str = "90d", trends: str = "365d"):
        """
        Args:
            name: Display name.
            key: Zabbix item key, e.g. ``system.cpu.util[,,avg1]``. Used as UUID seed.
            host: Owner template or host technical name. Set automatically by add_item().
            type: Collection method; defaults to ZABBIX_PASSIVE.
            value_type: Data type of collected value; defaults to UNSIGNED.
            history: History retention period, e.g. ``"90d"``.
            trends: Trend retention period, e.g. ``"365d"``.
        """
        super().__init__(name, uuid_seed=key)
        self.key = key
        self._host = host
        self.type = type
        self.value_type = value_type
        self.history = history
        self.trends = trends
        self.triggers: list[Trigger] = []

    def add_trigger(self, name: str, fn: str, op: str, threshold,
                    fn_args: tuple = (),
                    priority: TriggerPriority = TriggerPriority.NOT_CLASSIFIED,
                    description: str = None) -> Self:
        """Attach a trigger using a Zabbix function shorthand. Returns self for chaining.

        Builds expression ``fn(/host/key,fn_args...)op threshold``.

        Args:
            fn: Zabbix function name, e.g. ``"last"``, ``"min"``, ``"avg"``.
            op: Comparison operator string, e.g. ``">"``, ``"<"``, ``"="``.
            threshold: Comparison value; may be a Macro (rendered as ``{$NAME}``).
            fn_args: Extra function arguments, e.g. ``(10,)`` for ``min(/host/key,10)``.
            priority: TriggerPriority constant; defaults to NOT_CLASSIFIED.
            description: Optional trigger description.
        """
        expression = f"{self.expr(fn, *fn_args)}{op}{threshold}"
        self.triggers.append(Trigger(name, expression, priority, description))
        return self

    def link_interface(self, interface: HostInterface) -> Self:
        """Bind item to a specific host interface. Required for SNMP/IPMI items."""
        self.interface_ref = interface.interface_ref
        return self

    def link_value_map(self, value_map: ValueMap) -> Self:
        """Attach a value map to this item for display value translation."""
        self.valuemap = {"name": value_map.name}
        return self

    def expr(self, fn: str, *args) -> str:
        """Build a Zabbix expression string for this item.

        Returns a string like ``last(/host/key)`` or ``min(/host/key,10)``
        that can be concatenated to form trigger expressions.
        """
        base = f"{fn}(/{self._host}/{self.key})"
        if args:
            params = ",".join(str(a) for a in args)
            base = f"{fn}(/{self._host}/{self.key},{params})"
        return base

    @classmethod
    def from_dict(cls, data: dict, host: str = ""):
        item = cls(
            name=data["name"],
            key=data["key"],
            host=host,
            type=ItemType(data.get("type", "ZABBIX_PASSIVE")),
            value_type=ValueType(data.get("value_type", "UNSIGNED")),
            history=data.get("history", "90d"),
            trends=data.get("trends", "365d"),
        )
        for t in data.get("tags", []):
            item.add_tag(t["tag"], t.get("value", ""))
        for tr in data.get("triggers", []):
            item.triggers.append(Trigger.from_dict(tr))
        return item


class WithItems:
    def __init__(self):
        super().__init__()
        self.items: list[Item] = []

    def add_item(self, name: str, key: str,
                 type: ItemType = ItemType.ZABBIX_PASSIVE,
                 value_type: ValueType = ValueType.UNSIGNED,
                 history: str = "90d", trends: str = "365d") -> Item:
        """Create, register and return an Item owned by this entity. Raises on duplicate key."""
        if any(i.key == key for i in self.items):
            raise ValueError(
                f"Duplicate item key '{key}' on '{self.name}'"
            )
        item = Item(name, key, host=self.name, type=type,
                    value_type=value_type, history=history, trends=trends)
        self.items.append(item)
        return item