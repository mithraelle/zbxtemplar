from zbxtemplar.core import TemplarModule
from zbxtemplar.core.ZbxEntity import YesNo
from zbxtemplar.entities import Template, Item, Trigger, TriggerPriority, Graph, YAxisType, YAxisSide, Dashboard, \
    DashboardPage
from zbxtemplar.entities.DashboardWidget import ClassicGraph
from zbxtemplar.entities.DashboardWidget import Graph as dashGraph
from zbxtemplar.entities.DashboardWidget.ItemHistory import ItemHistory, ItemHistoryHeader
from zbxtemplar.entities.DashboardWidget.SimpleGraph import SimpleGraph
from zbxtemplar.entities.Item import ItemType
from zbxtemplar.entities.Template import ValueMap, ValueMapType


class SampleTemplate(TemplarModule):
    def __init__(self):
        super().__init__()

        template = Template(name="Test Template").add_tag("Service", "Testing")
        template.add_macro("MY_MACRO", 1, "Testing The Things")

        value_map = ValueMap("Test Map").add_mapping("1", "UP", ValueMapType.EQUAL).add_mapping("0", "DOWN", ValueMapType.EQUAL)
        template.add_value_map(value_map)

        item1 = Item("Item 1", "item.test[1]", template.name).add_tag("Service", "Testing 1")
        item1.add_trigger(name="Simple trigger", fn="min", op=">",
                          threshold=template.get_macro("MY_MACRO"),
                          priority=TriggerPriority.HIGH, description="A single item trigger",
                          fn_args=(10,))

        item2 = Item("Item 2", "item.test[2]", template.name, type=ItemType.ZABBIX_ACTIVE).add_tag("Service", "Testing 2")
        item2.set_value_map(value_map)

        item3 = Item(name="Item 3", key="item.test[3]", host=template.name, type=ItemType.TRAP).add_tag("Service", "Testing 3")

        template.add_item(item1).add_item(item2).add_item(item3)

        trigger_expr = (item1.expr("last") + ">" + template.get_macro("MY_MACRO")
                        + " and " + item2.expr("last") + " < " + template.get_macro("MY_MACRO"))

        graph = Graph("Test Graph", y_min=1, y_max_type=YAxisType.ITEM, y_max=item3)
        graph.add_item(item1, "1A7C11").add_item(item2, "274482", yaxisside=YAxisSide.RIGHT)

        self.templates = [template]
        self.triggers = [
            Trigger(name="Complex trigger", expression=trigger_expr,
                    priority=TriggerPriority.WARNING,
                    description="Trigger using two items"),
        ]
        self.graphs = [graph]

        first_page = DashboardPage(display_period=120)

        classic_graph_widget = ClassicGraph(template=template.name, graph=graph, x=0, y=0, width=36, height=5)
        first_page.add_widget(classic_graph_widget)

        item_history_widget = ItemHistory(x=36, y=0, width=18, height=5)
        item_history_widget.add_item(item2, "Item 2").add_item(item1, "Item 1")
        item_history_widget.show_timestamp(True).show_column_header(ItemHistoryHeader.HORIZONTAL)
        first_page.add_widget(item_history_widget)

        graph_widget = dashGraph.Graph(name="Complex graph", y=5, x=0, width=18, height=8)

        pattern_data_set = dashGraph.ItemPatternSet(label = "The Pattern", palette=0)
        pattern_data_set.add_pattern("item")
        pattern_draw_style = dashGraph.Bar()
        pattern_data_set.set_draw_style(pattern_draw_style)
        pattern_data_set.set_Y_axis(dashGraph.YAxis.RIGHT)
        graph_widget.add_data_set(pattern_data_set)

        items_data_set = dashGraph.ItemListSet(label = "Two Items")
        items_data_set.add_item(item3, "1A7C11").add_item(item2, "274482")
        graph_widget.add_data_set(items_data_set)

        graph_widget.set_legend(show_stats=True, show_aggregation=True, legend_lines=4, variable_legend_lines=True)
        first_page.add_widget(graph_widget)

        second_page = DashboardPage(name="Individual graphs")
        second_page.add_widget(SimpleGraph(name="Graph for Item1", item=item1, x=0, y=0, width=36, height=5))
        second_page.add_widget(SimpleGraph(item=item2, x=36, y=0, width=36, height=5))

        dashboard = Dashboard(name = "Sample Dashboard", auto_start=YesNo.NO, display_period=60)
        dashboard.add_page(first_page).add_page(second_page)
        template.add_dashboard(dashboard)


if __name__ == "__main__":
    import yaml
    module = SampleTemplate()
    print(yaml.dump(module.to_export(), default_flow_style=False, sort_keys=False))