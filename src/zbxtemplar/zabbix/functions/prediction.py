from zbxtemplar.zabbix.trigger_expression import TriggerFunction
from zbxtemplar.zabbix.Item import Item


class Forecast(TriggerFunction):
    """The future value, max, min, delta or avg of the item.

    Zabbix group: Predictive functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/prediction
    """
    def __init__(self, item: Item, period: str, time: str,
                 fit: str | None = None, mode: str | None = None):
        super().__init__("forecast", item, period, time, fit, mode)


class Timeleft(TriggerFunction):
    """The time in seconds needed for an item to reach the specified threshold.

    Zabbix group: Predictive functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/prediction
    """
    def __init__(self, item: Item, period: str, threshold: str,
                 fit: str | None = None):
        super().__init__("timeleft", item, period, threshold, fit)
