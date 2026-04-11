from enum import StrEnum

from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, YesNo
from zbxtemplar.zabbix import Item


class GraphType(StrEnum):
    NORMAL = "NORMAL"
    STACKED = "STACKED"
    PIE = "PIE"
    EXPLODED = "EXPLODED"


class YAxisType(StrEnum):
    CALCULATED = "CALCULATED"
    FIXED = "FIXED"
    ITEM = "ITEM"


class DrawType(StrEnum):
    SINGLE_LINE = "SINGLE_LINE"
    FILLED_REGION = "FILLED_REGION"
    BOLD_LINE = "BOLD_LINE"
    DOTTED_LINE = "DOTTED_LINE"
    DASHED_LINE = "DASHED_LINE"
    GRADIENT_LINE = "GRADIENT_LINE"


class CalcFnc(StrEnum):
    MIN = "MIN"
    AVG = "AVG"
    MAX = "MAX"
    ALL = "ALL"
    LAST = "LAST"


class GraphItemType(StrEnum):
    SIMPLE = "SIMPLE"
    GRAPH_SUM = "GRAPH_SUM"


class YAxisSide(StrEnum):
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
                 y_min: int | float | Item | str | None = None,
                 y_max: int | float | Item | str | None = None):
        super().__init__(name)
        self.type = type
        self.show_triggers = show_triggers
        self.show_legend = show_legend
        self.ymin_type_1 = y_min_type
        self.ymax_type_1 = y_max_type
        self._resolve_y("min", y_min, y_min_type)
        self._resolve_y("max", y_max, y_max_type)
        self.graph_items: list[GraphItem] = []

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
                 yaxisside: YAxisSide = YAxisSide.LEFT) -> Self:
        if order == -1:
            order = len(self.graph_items)
        self.graph_items.append(GraphItem(item, color, order, drawtype, calc_fnc, type, yaxisside))
        return self


class WithGraphs:
    def __init__(self):
        super().__init__()
        self._graphs: list[Graph] = []

    def add_graph(self, graph: Graph):
        if any(g.name == graph.name for g in self._graphs):
            raise ValueError(
                f"Duplicate graph '{graph.name}' on '{getattr(self, 'name', type(self).__name__)}'"
            )
        self._graphs.append(graph)
        return self

    @property
    def graphs(self):
        return list(self._graphs)