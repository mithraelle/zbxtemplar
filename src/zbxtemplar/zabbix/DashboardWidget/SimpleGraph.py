from zbxtemplar.zabbix import Item
from zbxtemplar.zabbix.Dashboard import Widget, WidgetField, WidgetFieldType


class SimpleGraph(Widget):
    def __init__(self, item: Item,
                 x: int = 0, y: int = 0, width: int = 12, height: int = 5,
                 name: str = ""):
        super().__init__(x, y, width, height, name)
        self._item = item

    @property
    def type(self) -> str:
        return "graph"

    def widget_fields(self) -> list:
        return [
            WidgetField(WidgetFieldType.INTEGER, "source_type", 1),
            WidgetField(WidgetFieldType.ITEM, "itemid.0", {"host": self._item._host, "key": self._item.key}),
        ]