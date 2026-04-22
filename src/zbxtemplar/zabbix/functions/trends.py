from zbxtemplar.zabbix.trigger_expression import TriggerFunction
from zbxtemplar.zabbix.Item import Item


class Baselinedev(TriggerFunction):
    """Returns the number of deviations (by stddevpop algorithm) between the last data period
    and the same data periods in preceding seasons.

    Zabbix group: Trend functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/trends
    """
    def __init__(self, item: Item, data_period: str, season_unit: str, num_seasons: int):
        super().__init__("baselinedev", item, data_period, season_unit, num_seasons)


class Baselinewma(TriggerFunction):
    """Calculates the baseline by averaging data from the same timeframe in multiple equal time
    periods ('seasons') using the weighted moving average algorithm.

    Zabbix group: Trend functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/trends
    """
    def __init__(self, item: Item, data_period: str, season_unit: str, num_seasons: int):
        super().__init__("baselinewma", item, data_period, season_unit, num_seasons)


class Trendavg(TriggerFunction):
    """The average of trend values within the defined time period.

    Zabbix group: Trend functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/trends
    """
    def __init__(self, item: Item, period: str):
        super().__init__("trendavg", item, period)


class Trendcount(TriggerFunction):
    """The number of successfully retrieved history values used to calculate the trend value
    within the defined time period.

    Zabbix group: Trend functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/trends
    """
    def __init__(self, item: Item, period: str):
        super().__init__("trendcount", item, period)


class Trendmax(TriggerFunction):
    """The maximum in trend values within the defined time period.

    Zabbix group: Trend functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/trends
    """
    def __init__(self, item: Item, period: str):
        super().__init__("trendmax", item, period)


class Trendmin(TriggerFunction):
    """The minimum in trend values within the defined time period.

    Zabbix group: Trend functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/trends
    """
    def __init__(self, item: Item, period: str):
        super().__init__("trendmin", item, period)


class Trendstl(TriggerFunction):
    """Returns the rate of anomalies during the detection period: number of anomaly values
    divided by total number of values, as a decimal between 0 and 1.

    Zabbix group: Trend functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/trends
    """
    def __init__(self, item: Item, detection_period: str, season: str, trend: str,
                 deviations: str | None = None, algorithm: str | None = None):
        super().__init__("trendstl", item, detection_period, season, trend, deviations, algorithm)


class Trendsum(TriggerFunction):
    """The sum of trend values within the defined time period.

    Zabbix group: Trend functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/trends
    """
    def __init__(self, item: Item, period: str):
        super().__init__("trendsum", item, period)
