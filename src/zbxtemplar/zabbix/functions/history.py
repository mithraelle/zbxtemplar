from zbxtemplar.zabbix.trigger_expression import TriggerFunction
from zbxtemplar.zabbix.Item import Item


class Change(TriggerFunction):
    def __init__(self, item: Item):
        super().__init__("change", item)


class Changecount(TriggerFunction):
    def __init__(self, item: Item, period: str, mode: str | None = None):
        super().__init__("changecount", item, period, mode)


class Count(TriggerFunction):
    def __init__(self, item: Item, period: str, operator: str | None = None, pattern: str | None = None):
        super().__init__("count", item, period, operator, pattern)


class Countunique(TriggerFunction):
    def __init__(self, item: Item, period: str, operator: str | None = None, pattern: str | None = None):
        super().__init__("countunique", item, period, operator, pattern)


class Find(TriggerFunction):
    def __init__(self, item: Item, period: str, operator: str, pattern: str):
        super().__init__("find", item, period, operator, pattern)


class First(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("first", item, period)


class Firstclock(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("firstclock", item, period)


class Fuzzytime(TriggerFunction):
    def __init__(self, item: Item, sec: str):
        super().__init__("fuzzytime", item, sec)


class Last(TriggerFunction):
    def __init__(self, item: Item, period: str | None = None):
        super().__init__("last", item, period)


class Lastclock(TriggerFunction):
    def __init__(self, item: Item, period: str | None = None):
        super().__init__("lastclock", item, period)


class Logeventid(TriggerFunction):
    def __init__(self, item: Item, pattern: str | None = None):
        super().__init__("logeventid", item, pattern)


class Logseverity(TriggerFunction):
    def __init__(self, item: Item):
        super().__init__("logseverity", item)


class Logsource(TriggerFunction):
    def __init__(self, item: Item, pattern: str | None = None):
        super().__init__("logsource", item, pattern)


class Logtimestamp(TriggerFunction):
    def __init__(self, item: Item, period: str | None = None):
        super().__init__("logtimestamp", item, period)


class Monodec(TriggerFunction):
    def __init__(self, item: Item, period: str, mode: str | None = None):
        super().__init__("monodec", item, period, mode)


class Monoinc(TriggerFunction):
    def __init__(self, item: Item, period: str, mode: str | None = None):
        super().__init__("monoinc", item, period, mode)


class Nodata(TriggerFunction):
    def __init__(self, item: Item, sec: str, mode: str | None = None):
        super().__init__("nodata", item, sec, mode)


class Percentile(TriggerFunction):
    def __init__(self, item: Item, period: str, percentage: int | float):
        super().__init__("percentile", item, period, percentage)


class Rate(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("rate", item, period)