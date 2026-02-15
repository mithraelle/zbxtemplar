from zbxtemplar.entities import Item
from zbxtemplar.entities.Dashboard import Widget, WidgetField, WidgetFieldType


class SimpleGraph(Widget):
    def __init__(self, item: Item,
                 x: int = 0, y: int = 0, width: int = 12, height: int = 5,
                 name: str = ""):
        super().__init__(x, y, width, height, name)
        self.fields.append(WidgetField(WidgetFieldType.INTEGER, "source_type", 1))
        self.fields.append(
            WidgetField(WidgetFieldType.ITEM, "itemid.0", {"host": item._host, "key": item.key})
        )

    @property
    def type(self) -> str:
        return "graph"

    def widget_fields(self) -> list:
        return self.fields