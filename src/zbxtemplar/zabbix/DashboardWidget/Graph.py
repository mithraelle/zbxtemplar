from abc import ABC
from enum import IntEnum
from typing import Self

from zbxtemplar.zabbix import Item
from zbxtemplar.zabbix.Dashboard import Widget, WidgetField, WidgetFieldType


class AggregateFunc(IntEnum):
    NO = 0
    MIN = 1
    MAX = 2
    AVG = 3
    COUNT = 4
    SUM = 5
    FIRST = 6
    LAST = 7


class AggregateBy(IntEnum):
    EACH_ITEM = 0
    DATA_SET = 1

class YAxis(IntEnum):
    LEFT = 0
    RIGHT = 1

class Approximation(IntEnum):
    MIN = 1
    AVG = 2
    MAX = 4
    ALL = 7

class MissedData(IntEnum):
    NONE = 0
    CONNECTED = 1
    TREAT_AS_0 = 2
    LAST_KNOWN = 3

class DataSource(IntEnum):
    AUTO = 0
    HISTORY = 1
    TRENDS = 2

class _BoundedInt:
    def __init__(self, lo: int, hi: int):
        self.lo, self.hi = lo, hi
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name)

    def __set__(self, obj, value):
        if not self.lo <= value <= self.hi:
            raise ValueError(f"{self.name}: must be {self.lo}..{self.hi}, got {value}")
        obj.__dict__[self.name] = value


class DrawStyle:
    transparency = _BoundedInt(0, 10)

    def __init__(self, transparency: int = 5):
        self.transparency = transparency

    def _list_fields(self, prefix: str) -> list[WidgetField]:
        fields = []
        for attr, value in vars(self).items():
            if attr.startswith("_") or value is None:
                continue
            if isinstance(value, int):
                fields.append(WidgetField(WidgetFieldType.INTEGER, f"{prefix}{attr}", str(value)))
            elif isinstance(value, str) and value != "":
                fields.append(WidgetField(WidgetFieldType.STRING, f"{prefix}{attr}", value))
        return fields


class Line(DrawStyle):
    width = _BoundedInt(1, 10)
    fill = _BoundedInt(0, 10)

    def __init__(self, stacked: bool = False, width: int = 1, transparency: int = 5, fill: int = 3, missed_data: MissedData = MissedData.NONE):
        super().__init__(transparency)
        self.type = 0
        self.stacked: int = 1 if stacked else 0
        self.width = width
        self.fill = fill
        self.missed_data = missed_data.value


class Points(DrawStyle):
    def __init__(self, point_size: int = 1, transparency: int = 5):
        super().__init__(transparency)
        self.pointsize = point_size
        self.type = 1


class Staircase(DrawStyle):
    width = _BoundedInt(1, 10)
    fill = _BoundedInt(0, 10)

    def __init__(self, stacked: bool = False, width: int = 1, transparency: int = 5, fill: int = 3, missed_data: MissedData = MissedData.NONE):
        super().__init__(transparency)
        self.type = 2
        self.stacked: int = 1 if stacked else 0
        self.width = width
        self.fill = fill
        self.missed_data = missed_data.value


class Bar(DrawStyle):
    def __init__(self, stacked: bool = False, transparency: int = 5):
        super().__init__(transparency)
        self.stacked: int = 1 if stacked else 0
        self.type = 3


class DataSet(ABC):
    def __init__(self, label: str = ""):
        self.data_set_label = label

    def set_Y_axis(self, yaxis: YAxis = YAxis.LEFT):
        self.axisy = yaxis.value

    def set_aggregate(self, func: AggregateFunc, interval: str = "1h",
                      aggregate_by: AggregateBy = AggregateBy.EACH_ITEM) -> Self:
        self.aggregate_function = func.value
        self.aggregate_interval = interval
        self.aggregate_grouping = aggregate_by.value
        return self

    def set_approximation(self, approximation: Approximation = Approximation.AVG) -> Self:
        self.approximation = approximation

    def set_draw_style(self, style: DrawStyle) -> Self:
        self._draw_style = style
        return self

    def _list_fields(self, prefix: str) -> list[WidgetField]:
        return []

    def to_dict(self, id: int) -> list[WidgetField]:
        fields = []
        prefix = f"ds.{id}."
        fields.extend(self._list_fields(prefix))
        for attr, value in vars(self).items():
            if attr.startswith("_") or value is None:
                continue
            if hasattr(value, '_list_fields'):
                fields.extend(value._list_fields(prefix))
            elif isinstance(value, int):
                fields.append(WidgetField(WidgetFieldType.INTEGER, f"{prefix}{attr}", str(value)))
            elif isinstance(value, str) and value != "":
                fields.append(WidgetField(WidgetFieldType.STRING, f"{prefix}{attr}", value))
        return fields


class ItemListSet(DataSet):
    def __init__(self, label: str = ""):
        super().__init__(label)
        self._items: list[tuple[Item, str]] = []
        self.dataset_type = 0

    def add_item(self, item: Item, color: str) -> Self:
        self._items.append((item, color))
        return self

    def _list_fields(self, prefix: str) -> list[WidgetField]:
        fields = []
        for i, (item, color) in enumerate(self._items):
            fields.append(WidgetField(WidgetFieldType.ITEM, f"{prefix}itemids.{i}", {"host": item._host, "key": item.key}))
            fields.append(WidgetField(WidgetFieldType.STRING, f"{prefix}color.{i}", color))
        return fields


class ItemPatternSet(DataSet):
    color_palette = _BoundedInt(0, 11)

    def __init__(self, *, color: str = None, palette: int = None, label: str = ""):
        super().__init__(label)
        if (color is None) == (palette is None):
            raise ValueError("Specify exactly one of color or palette")
        self.color = color
        self.color_palette = palette
        self._patterns: list[str] = []
        self.dataset_type = 1

    def add_pattern(self, *patterns: str) -> Self:
        self._patterns.extend(patterns)
        return self

    def _list_fields(self, prefix: str) -> list[WidgetField]:
        fields = []
        for i, pattern in enumerate(self._patterns):
            fields.append(WidgetField(WidgetFieldType.STRING, f"{prefix}items.{i}", pattern))
        return fields


class Graph(Widget):
    percentile_left_value = _BoundedInt(1, 100)
    percentile_right_value = _BoundedInt(1, 100)
    legend_lines = _BoundedInt(1, 10)
    legend_columns = _BoundedInt(1, 4)

    def __init__(self, x: int = 0, y: int = 0, width: int = 12, height: int = 5,
                 name: str = ""):
        super().__init__(x, y, width, height, name)
        self._data_sets: list[DataSet] = []

    def add_data_set(self, ds: DataSet) -> Self:
        self._data_sets.append(ds)
        return self

    @property
    def type(self) -> str:
        return "svggraph"

    def set_display_options(self, source: DataSource = DataSource.AUTO,
                            triggers: bool = False, working_time: bool = False,
                            percentline_left: int = None,
                            percentline_right: int = None) -> Self:
        self.source = source.value
        self.simple_triggers = int(triggers)
        self.working_time = int(working_time)
        if percentline_left is not None:
            self.percentile_left = 1
            self.percentile_left_value = percentline_left
        if percentline_right is not None:
            self.percentile_right = 1
            self.percentile_right_value = percentline_right
        return self

    def set_legend(self, show_stats: bool = False, show_aggregation: bool = False,
                   variable_legend_lines: bool = False,
                   legend_lines: int = 1, legend_columns: int = 1) -> Self:
        self.legend = 1
        self.legend_statistic = int(show_stats)
        self.legend_aggregation = int(show_aggregation)
        self.legend_lines_mode = int(variable_legend_lines)
        self.legend_lines = legend_lines
        self.legend_columns = legend_columns
        return self

    def widget_fields(self) -> list:
        fields = []
        for ds_id, ds in enumerate(self._data_sets):
            fields.extend(ds.to_dict(ds_id))
        for attr, value in vars(self).items():
            if attr.startswith("_") or value is None:
                continue
            if isinstance(value, int):
                fields.append(WidgetField(WidgetFieldType.INTEGER, attr, str(value)))
            elif isinstance(value, str) and value != "":
                fields.append(WidgetField(WidgetFieldType.STRING, attr, value))
        return fields