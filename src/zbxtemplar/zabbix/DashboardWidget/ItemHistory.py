from enum import Enum

from zbxtemplar.zabbix import Item
from zbxtemplar.zabbix.Dashboard import Widget, WidgetField, WidgetFieldType

class ItemHistoryHeader(str, Enum):
    NO = 0
    HORIZONTAL = 1
    VERTICAL = 2

class ItemHistory(Widget):
    def __init__(self, x: int = 0, y: int = 0, width: int = 12, height: int = 5,
                 name: str = ""):
        super().__init__(x, y, width, height, name)
        self._items = []
        self._show_timestamp = None
        self._show_column_header = None

    @property
    def type(self) -> str:
        return "itemhistory"

    def widget_fields(self) -> list:
        fields = []
        for i, (item, col_name) in enumerate(self._items):
            prefix = f"columns.{i}."
            fields.append(WidgetField(WidgetFieldType.ITEM, f"{prefix}itemid", {"host": item._host, "key": item.key}))
            fields.append(WidgetField(WidgetFieldType.STRING, f"{prefix}name", col_name))
        if self._show_timestamp is not None:
            fields.append(WidgetField(WidgetFieldType.INTEGER, "show_timestamp", str(int(self._show_timestamp))))
        if self._show_column_header is not None:
            fields.append(WidgetField(WidgetFieldType.INTEGER, "show_column_header", str(self._show_column_header.value)))
        return fields

    def add_item(self, item: Item, name: str = ""):
        self._items.append((item, name))
        return self

    def show_timestamp(self, show: bool = True):
        self._show_timestamp = show
        return self

    def show_column_header(self, header: ItemHistoryHeader = ItemHistoryHeader.NO):
        self._show_column_header = header
        return self