from zbxtemplar.zabbix.trigger_expression import TriggerFunction
from zbxtemplar.zabbix.Item import Item


class Baselinedev(TriggerFunction):
    def __init__(self, item: Item, data_period: str, season_unit: str, num_seasons: int):
        super().__init__("baselinedev", item, data_period, season_unit, num_seasons)


class Baselinewma(TriggerFunction):
    def __init__(self, item: Item, data_period: str, season_unit: str, num_seasons: int):
        super().__init__("baselinewma", item, data_period, season_unit, num_seasons)


class Trendavg(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("trendavg", item, period)


class Trendcount(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("trendcount", item, period)


class Trendmax(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("trendmax", item, period)


class Trendmin(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("trendmin", item, period)


class Trendstl(TriggerFunction):
    def __init__(self, item: Item, detection_period: str, season: str, trend: str,
                 deviations: str | None = None, algorithm: str | None = None):
        super().__init__("trendstl", item, detection_period, season, trend, deviations, algorithm)


class Trendsum(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("trendsum", item, period)