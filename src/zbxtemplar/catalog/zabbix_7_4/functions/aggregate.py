from zbxtemplar.zabbix.trigger_expression import TriggerFunction
from zbxtemplar.zabbix.Item import Item


# --- Aggregate functions (item history or foreach result) ---

class Avg(TriggerFunction):
    """The average value of an item within the defined evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item_or_foreach: Item | TriggerFunction, period: str | None = None):
        super().__init__("avg", item_or_foreach, period)


class BucketPercentile(TriggerFunction):
    """Calculates the percentile from the buckets of a histogram.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item_filter: str, time_period: str, percentage: int | float):
        super().__init__("bucket_percentile", item_filter, time_period, percentage)


class Count(TriggerFunction):
    """The count of values in an array returned by a foreach function.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, foreach_result: TriggerFunction):
        super().__init__("count", foreach_result)


class HistogramQuantile(TriggerFunction):
    """Calculates the phi-quantile from the buckets of a histogram.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, phi: int | float, bucket_rate_foreach: TriggerFunction):
        super().__init__("histogram_quantile", phi, bucket_rate_foreach)


class ItemCount(TriggerFunction):
    """The count of existing items in configuration that match the filter criteria.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item_filter: str):
        super().__init__("item_count", item_filter)


class Kurtosis(TriggerFunction):
    """The "tailedness" of the probability distribution in collected values within the defined
    evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item: Item, period: str):
        super().__init__("kurtosis", item, period)


class Mad(TriggerFunction):
    """The median absolute deviation in collected values within the defined evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item: Item, period: str):
        super().__init__("mad", item, period)


class Max(TriggerFunction):
    """The highest value of an item within the defined evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item_or_foreach: Item | TriggerFunction, period: str | None = None):
        super().__init__("max", item_or_foreach, period)


class Min(TriggerFunction):
    """The lowest value of an item within the defined evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item_or_foreach: Item | TriggerFunction, period: str | None = None):
        super().__init__("min", item_or_foreach, period)


class Skewness(TriggerFunction):
    """The asymmetry of the probability distribution in collected values within the defined
    evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item: Item, period: str):
        super().__init__("skewness", item, period)


class Stddevpop(TriggerFunction):
    """The population standard deviation in collected values within the defined evaluation
    period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item: Item, period: str):
        super().__init__("stddevpop", item, period)


class Stddevsamp(TriggerFunction):
    """The sample standard deviation in collected values within the defined evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item: Item, period: str):
        super().__init__("stddevsamp", item, period)


class Sum(TriggerFunction):
    """The sum of collected values within the defined evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item_or_foreach: Item | TriggerFunction, period: str | None = None):
        super().__init__("sum", item_or_foreach, period)


class Sumofsquares(TriggerFunction):
    """The sum of squares in collected values within the defined evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item: Item, period: str):
        super().__init__("sumofsquares", item, period)


class Varpop(TriggerFunction):
    """The population variance of collected values within the defined evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item: Item, period: str):
        super().__init__("varpop", item, period)


class Varsamp(TriggerFunction):
    """The sample variance of collected values within the defined evaluation period.

    Zabbix group: Aggregate functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate
    """
    def __init__(self, item: Item, period: str):
        super().__init__("varsamp", item, period)


# --- Foreach functions (calculated items only) ---

class AvgForeach(TriggerFunction):
    """Returns the average value for each item.

    Zabbix group: Foreach functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate/foreach
    """
    def __init__(self, item_filter: str, period: str):
        super().__init__("avg_foreach", item_filter, period)


class BucketRateForeach(TriggerFunction):
    """Returns pairs (bucket upper bound, rate value) suitable for use in histogram_quantile();
    the bucket upper bound is the item key parameter defined by the parameter number.

    Zabbix group: Foreach functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate/foreach
    """
    def __init__(self, item_filter: str, period: str, param_number: int):
        super().__init__("bucket_rate_foreach", item_filter, period, param_number)


class CountForeach(TriggerFunction):
    """Returns the number of values for each item.

    Zabbix group: Foreach functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate/foreach
    """
    def __init__(self, item_filter: str, period: str):
        super().__init__("count_foreach", item_filter, period)


class ExistsForeach(TriggerFunction):
    """Returns '1' for each enabled item.

    Zabbix group: Foreach functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate/foreach
    """
    def __init__(self, item_filter: str):
        super().__init__("exists_foreach", item_filter)


class LastForeach(TriggerFunction):
    """Returns the last value for each item.

    Zabbix group: Foreach functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate/foreach
    """
    def __init__(self, item_filter: str):
        super().__init__("last_foreach", item_filter)


class MaxForeach(TriggerFunction):
    """Returns the maximum value for each item.

    Zabbix group: Foreach functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate/foreach
    """
    def __init__(self, item_filter: str, period: str):
        super().__init__("max_foreach", item_filter, period)


class MinForeach(TriggerFunction):
    """Returns the minimum value for each item.

    Zabbix group: Foreach functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate/foreach
    """
    def __init__(self, item_filter: str, period: str):
        super().__init__("min_foreach", item_filter, period)


class SumForeach(TriggerFunction):
    """Returns the sum of values for each item.

    Zabbix group: Foreach functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/aggregate/foreach
    """
    def __init__(self, item_filter: str, period: str):
        super().__init__("sum_foreach", item_filter, period)
