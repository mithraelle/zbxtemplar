from enum import Enum

from zbxtemplar.entities import Item
from zbxtemplar.entities.Dashboard import Widget, WidgetField, WidgetFieldType

class ItemHistoryHeader(str, Enum):
    NO = 0
    HORIZONTAL = 1
    VERTICAL = 2

class ItemHistory(Widget):
    def __init__(self, x: int = 0, y: int = 0, width: int = 12, height: int = 5,
                 name: str = ""):
        super().__init__(x, y, width, height, name)
        self._item_count = 0

    @property
    def type(self) -> str:
        return "itemhistory"

    def widget_fields(self) -> list:
        return self.fields

    def add_item(self, item: Item, name: str = ""):
        prefix = f"columns.{self._item_count}."
        self.fields.append(WidgetField(WidgetFieldType.ITEM, f"{prefix}itemid", {"host": item._host, "key": item.key}))
        self.fields.append(WidgetField(WidgetFieldType.STRING, f"{prefix}name", name))
        self._item_count += 1
        return self

    def show_timestamp(self, show: bool = True):
        self.fields.append(WidgetField(WidgetFieldType.INTEGER, "show_timestamp", str(int(show))))
        return self

    def show_column_header(self, header: ItemHistoryHeader = ItemHistoryHeader.NO):
        self.fields.append(WidgetField(WidgetFieldType.INTEGER, "show_column_header", str(header.value)))
        return self