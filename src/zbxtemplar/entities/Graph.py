from enum import Enum
from typing import List, Union

from zbxtemplar.core.ZbxEntity import ZbxEntity, YesNo
from zbxtemplar.entities import Item


class GraphType(str, Enum):
    NORMAL = "NORMAL"
    STACKED = "STACKED"
    PIE = "PIE"
    EXPLODED = "EXPLODED"


class YAxisType(str, Enum):
    CALCULATED = "CALCULATED"
    FIXED = "FIXED"
    ITEM = "ITEM"


class DrawType(str, Enum):
    SINGLE_LINE = "SINGLE_LINE"
    FILLED_REGION = "FILLED_REGION"
    BOLD_LINE = "BOLD_LINE"
    DOTTED_LINE = "DOTTED_LINE"
    DASHED_LINE = "DASHED_LINE"
    GRADIENT_LINE = "GRADIENT_LINE"


class CalcFnc(str, Enum):
    MIN = "MIN"
    AVG = "AVG"
    MAX = "MAX"
    ALL = "ALL"
    LAST = "LAST"


class GraphItemType(str, Enum):
    SIMPLE = "SIMPLE"
    GRAPH_SUM = "GRAPH_SUM"


class YAxisSide(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class GraphItem:
    def __init__(self, item: Item, color: str, order: int = 0,
                 drawtype: DrawType = DrawType.SINGLE_LINE,
                 calc_fnc: CalcFnc = CalcFnc.AVG,
                 type: GraphItemType = GraphItemType.SIMPLE,
                 yaxisside: YAxisSide = YAxisSide.LEFT):
        self.item = {"host": item._host, "key": item.key}
        self.color = color
        self.sortorder = str(order)
        self.drawtype = drawtype
        self.calc_fnc = calc_fnc
        self.type = type
        self.yaxisside = yaxisside


class Graph(ZbxEntity):
    def __init__(self, name: str, type: GraphType = GraphType.NORMAL,
                 show_triggers: YesNo = YesNo.YES,
                 show_legend: YesNo = YesNo.YES,
                 y_min_type: YAxisType = YAxisType.CALCULATED,
                 y_max_type: YAxisType = YAxisType.CALCULATED,
                 y_min: Union[int, float, Item, str, None] = None,
                 y_max: Union[int, float, Item, str, None] = None):
        super().__init__(name)
        self.type = type
        self.show_triggers = show_triggers
        self.show_legend = show_legend
        self.ymin_type_1 = y_min_type
        self.ymax_type_1 = y_max_type
        self._resolve_y("min", y_min, y_min_type)
        self._resolve_y("max", y_max, y_max_type)
        self.graph_items: List[GraphItem] = []

    def _resolve_y(self, axis: str, value, axis_type: YAxisType):
        if axis_type == YAxisType.ITEM:
            if not isinstance(value, Item):
                raise ValueError(f"y_{axis}: type=ITEM requires an Item value")
            setattr(self, f"y{axis}_item_1", {"host": value._host, "key": value.key})
        elif value is not None:
            if isinstance(value, Item):
                raise ValueError(f"y_{axis}: Item value requires y_{axis}_type=ITEM")
            setattr(self, f"yaxis{axis}", str(value))

    def add_item(self, item: Item, color: str, order: int = -1,
                 drawtype: DrawType = DrawType.SINGLE_LINE,
                 calc_fnc: CalcFnc = CalcFnc.AVG,
                 type: GraphItemType = GraphItemType.SIMPLE,
                 yaxisside: YAxisSide = YAxisSide.LEFT) -> 'Graph':
        if order == -1:
            order = len(self.graph_items)
        self.graph_items.append(GraphItem(item, color, order, drawtype, calc_fnc, type, yaxisside))
        return self