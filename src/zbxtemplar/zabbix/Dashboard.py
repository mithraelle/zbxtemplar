from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Self

from zbxtemplar.zabbix.ZbxEntity import ZbxEntity, YesNo


class _WidgetRefCounter:
    _counter = 0

    @classmethod
    def next(cls) -> str:
        val = cls._counter
        cls._counter += 1
        chars = []
        for _ in range(5):
            chars.append(chr(ord('A') + val % 26))
            val //= 26
        return ''.join(reversed(chars))

    @classmethod
    def reset(cls):
        cls._counter = 0


class WidgetFieldType(StrEnum):
    INTEGER = "INTEGER"
    STRING = "STRING"
    ITEM = "ITEM"
    ITEM_PROTOTYPE = "ITEM_PROTOTYPE"
    GRAPH = "GRAPH"
    GRAPH_PROTOTYPE = "GRAPH_PROTOTYPE"
    MAP = "MAP"
    SERVICE = "SERVICE"
    SLA = "SLA"
    USER = "USER"
    ACTION = "ACTION"
    MEDIA_TYPE = "MEDIA_TYPE"


class WidgetField:
    def __init__(self, type: WidgetFieldType, name: str, value):
        self.type = type
        self.name = name
        self.value = value

    def to_dict(self):
        value = str(self.value) if isinstance(self.value, (int, float)) else self.value
        return {"type": self.type.value, "name": self.name, "value": value}


class Widget(ABC):
    def __init__(self, x: int, y: int, width: int, height: int, name: str = ""):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.fields: list[WidgetField] = [
            WidgetField(WidgetFieldType.STRING, "reference", _WidgetRefCounter.next())
        ]

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @abstractmethod
    def widget_fields(self) -> list:
        pass

    def to_dict(self):
        result = {"type": self.type}
        if self.name:
            result["name"] = self.name
        if self.x:
            result["x"] = str(self.x)
        if self.y:
            result["y"] = str(self.y)
        result["width"] = str(self.width)
        result["height"] = str(self.height)
        all_fields = self.fields + self.widget_fields()
        result["fields"] = [f.to_dict() for f in all_fields]
        return result


class DashboardPage:
    """A single page of a Zabbix template dashboard."""

    def __init__(self, name: str = "", display_period: int = 0):
        """
        Args:
            display_period: Slide rotation interval in seconds; 0 disables auto-rotation.
        """
        self.name = name
        self.display_period = display_period
        self.widgets: list[Widget] = []

    def link_widget(self, widget: Widget):
        """Link an existing widget to this page."""
        self.widgets.append(widget)

    def to_dict(self):
        result = {}
        if self.name:
            result["name"] = self.name
        if self.display_period:
            result["display_period"] = str(self.display_period)
        if self.widgets:
            result["widgets"] = [w.to_dict() for w in self.widgets]
        return result


class Dashboard(ZbxEntity):
    """Zabbix dashboard attached to a template."""

    def __init__(self, name: str, display_period: int = 0,
                 auto_start: YesNo = YesNo.YES):
        """
        Args:
            display_period: Default page slide interval in seconds.
            auto_start: Start the slideshow automatically (YesNo.YES or YesNo.NO).
        """
        super().__init__(name)
        self.display_period = str(display_period)
        self.auto_start = auto_start
        self.pages: list[DashboardPage] = []

    def add_page(self, name: str = "", display_period: int = 0) -> DashboardPage:
        """Create, register and return a new DashboardPage."""
        page = DashboardPage(name=name, display_period=display_period)
        self.pages.append(page)
        return page