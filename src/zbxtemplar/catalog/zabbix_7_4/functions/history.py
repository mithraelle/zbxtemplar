from zbxtemplar.zabbix.trigger_expression import TriggerFunction
from zbxtemplar.zabbix.Item import Item


class Change(TriggerFunction):
    """The amount of difference between the previous and latest value.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item):
        super().__init__("change", item)


class Changecount(TriggerFunction):
    """The number of changes between adjacent values within the defined evaluation period.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str, mode: str | None = None):
        super().__init__("changecount", item, period, mode)


class Count(TriggerFunction):
    """The number of values within the defined evaluation period.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str, operator: str | None = None, pattern: str | None = None):
        super().__init__("count", item, period, operator, pattern)


class Countunique(TriggerFunction):
    """The number of unique values within the defined evaluation period.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str, operator: str | None = None, pattern: str | None = None):
        super().__init__("countunique", item, period, operator, pattern)


class Find(TriggerFunction):
    """Find a value match within the defined evaluation period.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str, operator: str, pattern: str):
        super().__init__("find", item, period, operator, pattern)


class First(TriggerFunction):
    """The first (the oldest) value within the defined evaluation period.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str):
        super().__init__("first", item, period)


class Firstclock(TriggerFunction):
    """The timestamp of the first (the oldest) value within the defined evaluation period.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str):
        super().__init__("firstclock", item, period)


class Fuzzytime(TriggerFunction):
    """Check how much the passive agent time differs from the Zabbix server/proxy time.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, sec: str):
        super().__init__("fuzzytime", item, sec)


class Last(TriggerFunction):
    """The most recent value.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str | None = None):
        super().__init__("last", item, period)


class Lastclock(TriggerFunction):
    """The timestamp of the Nth most recent value within the defined evaluation period.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str | None = None):
        super().__init__("lastclock", item, period)


class Logeventid(TriggerFunction):
    """Check if the event ID of the last log entry matches a regular expression.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, pattern: str | None = None):
        super().__init__("logeventid", item, pattern)


class Logseverity(TriggerFunction):
    """The log severity of the last log entry.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item):
        super().__init__("logseverity", item)


class Logsource(TriggerFunction):
    """Check if log source of the last log entry matches a regular expression.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, pattern: str | None = None):
        super().__init__("logsource", item, pattern)


class Logtimestamp(TriggerFunction):
    """The log message timestamp of the Nth most recent log item value.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str | None = None):
        super().__init__("logtimestamp", item, period)


class Monodec(TriggerFunction):
    """Check if there has been a monotonous decrease in values.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str, mode: str | None = None):
        super().__init__("monodec", item, period, mode)


class Monoinc(TriggerFunction):
    """Check if there has been a monotonous increase in values.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str, mode: str | None = None):
        super().__init__("monoinc", item, period, mode)


class Nodata(TriggerFunction):
    """Check for no data received.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, sec: str, mode: str | None = None):
        super().__init__("nodata", item, sec, mode)


class Percentile(TriggerFunction):
    """The P-th percentile of a period, where P (percentage) is specified by the third
    parameter.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str, percentage: int | float):
        super().__init__("percentile", item, period, percentage)


class Rate(TriggerFunction):
    """The per-second average rate of the increase in a monotonically increasing counter within
    the defined time period.

    Zabbix group: History functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/history
    """
    def __init__(self, item: Item, period: str):
        super().__init__("rate", item, period)
