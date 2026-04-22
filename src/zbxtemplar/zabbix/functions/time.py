from zbxtemplar.zabbix.trigger_expression import TriggerFunction


class Date(TriggerFunction):
    """The current date in YYYYMMDD format.

    Zabbix group: Date and time functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/time
    """
    def __init__(self):
        super().__init__("date")


class Dayofmonth(TriggerFunction):
    """The day of month in range of 1 to 31.

    Zabbix group: Date and time functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/time
    """
    def __init__(self):
        super().__init__("dayofmonth")


class Dayofweek(TriggerFunction):
    """The day of week in range of 1 to 7.

    Zabbix group: Date and time functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/time
    """
    def __init__(self):
        super().__init__("dayofweek")


class Now(TriggerFunction):
    """The number of seconds since the Epoch (00:00:00 UTC, January 1, 1970).

    Zabbix group: Date and time functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/time
    """
    def __init__(self):
        super().__init__("now")


class Time(TriggerFunction):
    """The current time in HHMMSS format.

    Zabbix group: Date and time functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/time
    """
    def __init__(self):
        super().__init__("time")
