from zbxtemplar.entities.Dashboard import Widget, WidgetField, WidgetFieldType
from zbxtemplar.entities.Graph import Graph


class ClassicGraph(Widget):
    def __init__(self, template: str, graph: Graph,
                 x: int = 0, y: int = 0, width: int = 12, height: int = 5,
                 name: str = ""):
        super().__init__(x, y, width, height, name)
        self._template = template
        self._graph = graph

    @property
    def type(self) -> str:
        return "graph"

    def widget_fields(self) -> list:
        return [
            WidgetField(WidgetFieldType.GRAPH, "graphid.0", {"host": self._template, "name": self._graph.name}),
        ]