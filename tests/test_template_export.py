import yaml

import pytest

from zbxtemplar.modules import TemplarModule
from zbxtemplar.zabbix.ZbxEntity import YesNo
from zbxtemplar.zabbix import TriggerPriority, Graph, YAxisType, YAxisSide, HostGroup, functions
from zbxtemplar.zabbix.Host import AgentInterface
from zbxtemplar.zabbix.Template import TemplateGroup
from zbxtemplar.zabbix.DashboardWidget import Graph as dashGraph
from zbxtemplar.zabbix.DashboardWidget import ClassicGraph
from zbxtemplar.zabbix.DashboardWidget.ItemHistory import ItemHistory, ItemHistoryHeader
from zbxtemplar.zabbix.DashboardWidget.SimpleGraph import SimpleGraph
from zbxtemplar.zabbix.Item import ItemType
from zbxtemplar.zabbix.Template import ValueMapType
from tests.paths import REFERENCE_DIR

REFERENCE_COMBINED = REFERENCE_DIR / "combined.yml"
REFERENCE_TEMPLATES = REFERENCE_DIR / "templates.yml"
REFERENCE_HOSTS = REFERENCE_DIR / "hosts.yml"


class SampleTemplate(TemplarModule):
    def compose(self):
        template = self.add_template(name="Test Template", groups=[TemplateGroup("Templar Templates")]).add_tag("Service", "Testing")
        template_macro = template.add_macro("MY_MACRO", 1, "Testing The Things")

        value_map = template.add_value_map("Test Map").add_mapping("1", "UP", ValueMapType.EQUAL).add_mapping("0", "DOWN",
                                                                                                               ValueMapType.EQUAL)

        item1 = template.add_item("Item 1", "item.test[1]").add_tag("Service", "Testing 1")
        template.add_trigger(name="Simple trigger",
                             expression=functions.aggregate.Min(item1, "10") > template_macro,
                             priority=TriggerPriority.HIGH, description="A single item trigger")

        item2 = template.add_item("Item 2", "item.test[2]", type=ItemType.ZABBIX_ACTIVE).add_tag("Service", "Testing 2")
        item2.link_value_map(value_map)

        item3 = template.add_item("Item 3", "item.test[3]", type=ItemType.TRAP).add_tag("Service", "Testing 3")

        trigger_expr = ((functions.history.Last(item1) > template.get_macro("MY_MACRO"))
                        & (functions.history.Last(item2) < template.get_macro("MY_MACRO")))

        graph = template.add_graph("Test Graph", y_min=1, y_max_type=YAxisType.ITEM, y_max=item3)
        graph.link_item(item1, "1A7C11").link_item(item2, "274482", yaxisside=YAxisSide.RIGHT)

        template.add_trigger(name="Complex trigger", expression=trigger_expr,
                             priority=TriggerPriority.WARNING,
                             description="Trigger using two items")

        graph_widget = ClassicGraph(template=template.name, graph=graph, x=0, y=0, width=36, height=5)

        item_history_widget = ItemHistory(x=36, y=0, width=18, height=5)
        item_history_widget.link_item(item2, "Item 2").link_item(item1, "Item 1")
        item_history_widget.show_timestamp(True).show_column_header(ItemHistoryHeader.HORIZONTAL)

        svgg_widget = dashGraph.Graph(name="Complex graph", y=5, x=0, width=18, height=8)

        pattern_data_set = dashGraph.ItemPatternSet(label="The Pattern", palette=0)
        pattern_data_set.add_pattern("item")
        pattern_draw_style = dashGraph.Bar()
        pattern_data_set.set_draw_style(pattern_draw_style)
        pattern_data_set.set_Y_axis(dashGraph.YAxis.RIGHT)
        svgg_widget.link_data_set(pattern_data_set)

        items_data_set = dashGraph.ItemListSet(label="Two Items")
        items_data_set.link_item(item3, "1A7C11").link_item(item2, "274482")
        svgg_widget.link_data_set(items_data_set)

        svgg_widget.set_legend(show_stats=True, show_aggregation=True, legend_lines=4, variable_legend_lines=True)

        dashboard = template.add_dashboard("Sample Dashboard", auto_start=YesNo.NO, display_period=60)
        first_page = dashboard.add_page(display_period=120)
        first_page.link_widget(graph_widget)
        first_page.link_widget(item_history_widget)
        first_page.link_widget(svgg_widget)

        second_page = dashboard.add_page(name="Individual graphs")
        second_page.link_widget(SimpleGraph(name="Graph for Item1", item=item1, x=0, y=0, width=36, height=5))
        second_page.link_widget(SimpleGraph(item=item2, x=36, y=0, width=36, height=5))

        host = self.add_host("Templar Host", groups=[HostGroup("Templar Hosts")])
        host_macro = host.add_macro("MY_HOST_MACRO", 1, "Testing The Host Macro")
        host.link_template(template)
        host_item = host.add_item("Item Own", "item.test[own]").add_tag("Service", "Testing Host")
        host_if1 = AgentInterface()
        host.link_interface(host_if1)
        host_item.link_interface(host_if1)
        host.add_trigger(name="Host Simple trigger",
                         expression=functions.aggregate.Min(host_item, 10) > host_macro,
                         priority=TriggerPriority.HIGH, description="A single host item trigger")

        host_graph = host.add_graph("Host Graph")
        host_graph.link_item(host_item, "1A7C11")

        host_trigger_expr = ((functions.history.Last(host_item) > host_macro)
                             & (functions.history.Last(host_item) < host.get_macro("MY_MACRO")))
        host.add_trigger(name="Host Complex trigger", expression=host_trigger_expr,
                         priority=TriggerPriority.WARNING,
                         description="Host trigger using two items")

class EmptyTemplar(TemplarModule):
    def compose(self):
        pass


@pytest.fixture(scope="module")
def module():
    return SampleTemplate()


def test_add_template_constructs_and_returns_template():
    module = EmptyTemplar()

    template = module.add_template("Standalone Template", groups=[TemplateGroup("Templar Templates")])

    assert template.name == "Standalone Template"
    assert module.templates == [template]


def test_add_host_constructs_and_returns_host():
    module = EmptyTemplar()

    host = module.add_host("Standalone Host", groups=[HostGroup("Templar Hosts")])

    assert host.name == "Standalone Host"
    assert module.hosts == [host]


def test_add_template_rejects_duplicate_name():
    module = EmptyTemplar()
    module.add_template("Duplicate Template", groups=[TemplateGroup("Templar Templates")])

    with pytest.raises(ValueError, match="duplicate template 'Duplicate Template'"):
        module.add_template("Duplicate Template", groups=[TemplateGroup("Other Templates")])


def test_add_host_rejects_duplicate_name():
    module = EmptyTemplar()
    module.add_host("Duplicate Host", groups=[HostGroup("Templar Hosts")])

    with pytest.raises(ValueError, match="duplicate host 'Duplicate Host'"):
        module.add_host("Duplicate Host", groups=[HostGroup("Other Hosts")])


def test_combined_export_matches_reference(module):
    generated = module.to_export()

    with open(REFERENCE_COMBINED) as f:
        expected = yaml.safe_load(f)

    assert generated == expected


def test_templates_export_matches_reference(module):
    generated = module.export_templates()

    with open(REFERENCE_TEMPLATES) as f:
        expected = yaml.safe_load(f)

    assert generated == expected


def test_hosts_export_matches_reference(module):
    generated = module.export_hosts()

    with open(REFERENCE_HOSTS) as f:
        expected = yaml.safe_load(f)

    assert generated == expected
