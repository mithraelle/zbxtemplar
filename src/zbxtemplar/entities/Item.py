from enum import Enum
from typing import List, Union

from zbxtemplar.core.ZbxEntity import ZbxEntity, WithTags
from zbxtemplar.entities.Trigger import Trigger, TriggerPriority


class ItemType(str, Enum):
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


class ValueType(str, Enum):
    FLOAT = "FLOAT"
    CHAR = "CHAR"
    LOG = "LOG"
    UNSIGNED = "UNSIGNED"
    TEXT = "TEXT"
    BINARY = "BINARY"


class Item(ZbxEntity, WithTags):
    def __init__(self, name: str, key: str, host: str,
                 type: ItemType = ItemType.ZABBIX_PASSIVE,
                 value_type: ValueType = ValueType.UNSIGNED,
                 history: str = "90d", trends: str = "365d"):
        super().__init__(name, uuid_seed=key)
        self.key = key
        self._host = host
        self.type = type
        self.value_type = value_type
        self.history = history
        self.trends = trends
        self.triggers: List[Trigger] = []

    def add_trigger(self, name: str, fn: str, op: str, threshold,
                    fn_args: tuple = (),
                    priority: TriggerPriority = TriggerPriority.NOT_CLASSIFIED,
                    description: str = None) -> 'Item':
        expression = f"{self.expr(fn, *fn_args)}{op}{threshold}"
        self.triggers.append(Trigger(name, expression, priority, description))
        return self

    def set_value_map(self, value_map) -> 'Item':
        self.valuemap = {"name": value_map.name}
        return self

    def expr(self, fn: str, *args) -> str:
        base = f"{fn}(/{self._host}/{self.key})"
        if args:
            params = ",".join(str(a) for a in args)
            base = f"{fn}(/{self._host}/{self.key},{params})"
        return base