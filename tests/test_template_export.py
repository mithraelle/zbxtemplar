from pathlib import Path

import yaml

from zbxtemplar.core import TemplarModule
from zbxtemplar.core.ZbxEntity import YesNo
from zbxtemplar.entities import Template, Item, Trigger, TriggerPriority, Graph, YAxisType, YAxisSide, Dashboard, \
    DashboardPage
from zbxtemplar.entities.DashboardWidget import ClassicGraph
from zbxtemplar.entities.DashboardWidget.ItemHistory import ItemHistory, ItemHistoryHeader
from zbxtemplar.entities.DashboardWidget.SimpleGraph import SimpleGraph
from zbxtemplar.entities.Item import ItemType

REFERENCE_PATH = Path(__file__).parent / "reference_template.yml"


class TestTemplate(TemplarModule):
    def __init__(self):
        super().__init__()

        template = Template(name="Test Template").add_tag("Service", "Testing")
        template.add_macro("MY_MACRO", 1, "Testing The Things")

        item1 = Item("Item 1", "item.test[1]", template.name).add_tag("Service", "Testing 1")
        item1.add_trigger(name="Simple trigger", fn="min", op=">",
                          threshold=template.get_macro("MY_MACRO"),
                          priority=TriggerPriority.HIGH, description="A single item trigger",
                          fn_args=(10,))

        item2 = Item("Item 2", "item.test[2]", template.name, type=ItemType.ZABBIX_ACTIVE).add_tag("Service", "Testing 2")
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

        graph_widget = ClassicGraph(template=template.name, graph=graph, x=0, y=0, width=36, height=5)
        first_page = DashboardPage(display_period=120)
        first_page.add_widget(graph_widget)

        item_history_widget = ItemHistory(x=36, y=0, width=18, height=5)
        item_history_widget.add_item(item2, "Item 2").add_item(item1, "Item 1")
        item_history_widget.show_timestamp(True).show_column_header(ItemHistoryHeader.HORIZONTAL)
        first_page.add_widget(item_history_widget)

        second_page = DashboardPage(name="Individual graphs")
        second_page.add_widget(SimpleGraph(name="Graph for Item1", item=item1, x=0, y=0, width=36, height=5))
        second_page.add_widget(SimpleGraph(item=item2, x=36, y=0, width=36, height=5))

        dashboard = Dashboard(name="Sample Dashboard", auto_start=YesNo.NO, display_period=60)
        dashboard.add_page(first_page).add_page(second_page)
        template.add_dashboard(dashboard)


def test_template_matches_reference():
    module = TestTemplate()
    generated = module.to_export()

    with open(REFERENCE_PATH) as f:
        expected = yaml.safe_load(f)

    assert generated == expected