from zbxtemplar.zabbix.trigger_expression import TriggerFunction
from zbxtemplar.zabbix.Item import Item


class Forecast(TriggerFunction):
    def __init__(self, item: Item, period: str, time: str,
                 fit: str | None = None, mode: str | None = None):
        super().__init__("forecast", item, period, time, fit, mode)


class Timeleft(TriggerFunction):
    def __init__(self, item: Item, period: str, threshold: str,
                 fit: str | None = None):
        super().__init__("timeleft", item, period, threshold, fit)