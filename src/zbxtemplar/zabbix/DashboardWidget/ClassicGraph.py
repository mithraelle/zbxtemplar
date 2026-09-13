from zbxtemplar.zabbix.Dashboard import Widget, WidgetField, WidgetFieldType
from zbxtemplar.zabbix.Graph import Graph


class ClassicGraph(Widget):
    def __init__(self, graph: Graph, template: str = "",
                 x: int = 0, y: int = 0, width: int = 12, height: int = 5,
                 name: str = ""):
        """
        Args:
            template: Template owning the referenced graph; defaults to the
                template of the dashboard this widget is linked into.
        """
        super().__init__(x, y, width, height, name)
        self._template = template
        self._graph = graph

    @property
    def type(self) -> str:
        return "graph"

    def widget_fields(self) -> list:
        return [
            WidgetField(WidgetFieldType.GRAPH, "graphid.0", {"host": self._template or self._host, "name": self._graph.name}),
        ]