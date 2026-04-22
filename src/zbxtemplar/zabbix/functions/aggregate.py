from zbxtemplar.zabbix.trigger_expression import TriggerFunction
from zbxtemplar.zabbix.Item import Item


# --- Aggregate functions (item history or foreach result) ---

class Avg(TriggerFunction):
    def __init__(self, item_or_foreach: Item | TriggerFunction, period: str | None = None):
        super().__init__("avg", item_or_foreach, period)


class BucketPercentile(TriggerFunction):
    def __init__(self, item_filter: str, time_period: str, percentage: int | float):
        super().__init__("bucket_percentile", item_filter, time_period, percentage)


class Count(TriggerFunction):
    def __init__(self, foreach_result: TriggerFunction):
        super().__init__("count", foreach_result)


class HistogramQuantile(TriggerFunction):
    def __init__(self, phi: int | float, bucket_rate_foreach: TriggerFunction):
        super().__init__("histogram_quantile", phi, bucket_rate_foreach)


class ItemCount(TriggerFunction):
    def __init__(self, item_filter: str):
        super().__init__("item_count", item_filter)


class Kurtosis(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("kurtosis", item, period)


class Mad(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("mad", item, period)


class Max(TriggerFunction):
    def __init__(self, item_or_foreach: Item | TriggerFunction, period: str | None = None):
        super().__init__("max", item_or_foreach, period)


class Min(TriggerFunction):
    def __init__(self, item_or_foreach: Item | TriggerFunction, period: str | None = None):
        super().__init__("min", item_or_foreach, period)


class Skewness(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("skewness", item, period)


class Stddevpop(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("stddevpop", item, period)


class Stddevsamp(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("stddevsamp", item, period)


class Sum(TriggerFunction):
    def __init__(self, item_or_foreach: Item | TriggerFunction, period: str | None = None):
        super().__init__("sum", item_or_foreach, period)


class Sumofsquares(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("sumofsquares", item, period)


class Varpop(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("varpop", item, period)


class Varsamp(TriggerFunction):
    def __init__(self, item: Item, period: str):
        super().__init__("varsamp", item, period)


# --- Foreach functions (calculated items only) ---

class AvgForeach(TriggerFunction):
    def __init__(self, item_filter: str, period: str):
        super().__init__("avg_foreach", item_filter, period)


class BucketRateForeach(TriggerFunction):
    def __init__(self, item_filter: str, period: str, param_number: int):
        super().__init__("bucket_rate_foreach", item_filter, period, param_number)


class CountForeach(TriggerFunction):
    def __init__(self, item_filter: str, period: str):
        super().__init__("count_foreach", item_filter, period)


class ExistsForeach(TriggerFunction):
    def __init__(self, item_filter: str):
        super().__init__("exists_foreach", item_filter)


class LastForeach(TriggerFunction):
    def __init__(self, item_filter: str):
        super().__init__("last_foreach", item_filter)


class MaxForeach(TriggerFunction):
    def __init__(self, item_filter: str, period: str):
        super().__init__("max_foreach", item_filter, period)


class MinForeach(TriggerFunction):
    def __init__(self, item_filter: str, period: str):
        super().__init__("min_foreach", item_filter, period)


class SumForeach(TriggerFunction):
    def __init__(self, item_filter: str, period: str):
        super().__init__("sum_foreach", item_filter, period)