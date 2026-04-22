from zbxtemplar.zabbix.trigger_expression import TriggerFunction


class Date(TriggerFunction):
    def __init__(self):
        super().__init__("date")


class Dayofmonth(TriggerFunction):
    def __init__(self):
        super().__init__("dayofmonth")


class Dayofweek(TriggerFunction):
    def __init__(self):
        super().__init__("dayofweek")


class Now(TriggerFunction):
    def __init__(self):
        super().__init__("now")


class Time(TriggerFunction):
    def __init__(self):
        super().__init__("time")