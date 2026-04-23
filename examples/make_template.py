from zbxtemplar.modules import TemplarModule
from zbxtemplar.zabbix.ZbxEntity import YesNo
from zbxtemplar.zabbix import TriggerPriority, YAxisType, YAxisSide, MacroType
from zbxtemplar.zabbix.DashboardWidget import ClassicGraph
from zbxtemplar.zabbix.DashboardWidget import Graph as dashGraph
from zbxtemplar.zabbix.DashboardWidget.ItemHistory import ItemHistory, ItemHistoryHeader
from zbxtemplar.zabbix.DashboardWidget.SimpleGraph import SimpleGraph
from zbxtemplar.zabbix.Item import ItemType
from zbxtemplar.zabbix.Template import TemplateGroup, ValueMapType
from zbxtemplar.zabbix.Host import HostGroup, AgentInterface
from zbxtemplar.zabbix import functions
from zbxtemplar.zabbix.Inventory import InventoryField, InventoryMode


class SampleTemplate(TemplarModule):
    def compose(self):
        self.add_macro("TEMPLAR_GLOBAL_MACRO", 1, "Global macro")

        template_group = TemplateGroup("Templar Templates")
        host_group = HostGroup("Templar Hosts")

        template = (self.add_template("Test Template", groups=[template_group])
                    .add_tag("Service","Testing"))
        template_macro = template.add_macro("MY_MACRO", 1, "Testing The Things")

        value_map = (template.add_value_map("Test Map").add_mapping("1", "UP", ValueMapType.EQUAL)
                     .add_mapping("0", "DOWN", ValueMapType.EQUAL))

        item1 = template.add_item("Item 1", "item.test[1]").add_tag("Service", "Testing 1")
        template.add_trigger(name="Simple trigger",
                             expression=functions.aggregate.Min(item1, "10") > template_macro,
                             priority=TriggerPriority.HIGH, description="A single item trigger")

        item2 = (template.add_item("Item 2", "item.test[2]", type=ItemType.ZABBIX_ACTIVE)
                 .add_tag("Service", "Testing 2"))
        item2.link_value_map(value_map)

        item3 = (template.add_item("Item 3", "item.test[3]", type=ItemType.TRAP)
                 .add_tag("Service", "Testing 3"))

        trigger_expr = ((functions.history.Last(item1) > template.get_macro("MY_MACRO"))
                              & (functions.history.Last(item2) < template.get_macro("MY_MACRO")))

        template.add_trigger(name="Complex trigger", expression=trigger_expr,
                             priority=TriggerPriority.WARNING,
                             description="Trigger using two items")

        graph = template.add_graph("Test Graph", y_min=1, y_max_type=YAxisType.ITEM, y_max=item3)
        graph.link_item(item1, "1A7C11").link_item(item2, "274482", yaxisside=YAxisSide.RIGHT)


        classic_graph_widget = ClassicGraph(template=template.name, graph=graph, x=0, y=0, width=36, height=5)

        item_history_widget = ItemHistory(x=36, y=0, width=18, height=5)
        item_history_widget.link_item(item2, "Item 2").link_item(item1, "Item 1")
        item_history_widget.show_timestamp(True).show_column_header(ItemHistoryHeader.HORIZONTAL)

        graph_widget = dashGraph.Graph(name="Complex graph", y=5, x=0, width=18, height=8)

        pattern_data_set = dashGraph.ItemPatternSet(label="The Pattern", palette=0)
        pattern_data_set.add_pattern("item")
        pattern_draw_style = dashGraph.Bar()
        pattern_data_set.set_draw_style(pattern_draw_style)
        pattern_data_set.set_Y_axis(dashGraph.YAxis.RIGHT)
        graph_widget.link_data_set(pattern_data_set)

        items_data_set = dashGraph.ItemListSet(label="Two Items")
        items_data_set.link_item(item3, "1A7C11").link_item(item2, "274482")
        graph_widget.link_data_set(items_data_set)

        graph_widget.set_legend(show_stats=True, show_aggregation=True, legend_lines=4, variable_legend_lines=True)

        dashboard = template.add_dashboard("Sample Dashboard", auto_start=YesNo.NO, display_period=60)
        first_page = dashboard.add_page(display_period=120)
        first_page.link_widget(classic_graph_widget)
        first_page.link_widget(item_history_widget)
        first_page.link_widget(graph_widget)

        second_page = dashboard.add_page(name="Individual graphs")
        second_page.link_widget(SimpleGraph(name="Graph for Item1", item=item1, x=0, y=0, width=36, height=5))
        second_page.link_widget(SimpleGraph(item=item2, x=36, y=0, width=36, height=5))

        host = self.add_host("Templar Host", groups=[host_group])
        host.set_inventory_mode(InventoryMode.MANUAL).set_inventory(InventoryField.OS, "Linux").set_inventory(InventoryField.NAME, "Templar Test")

        host_macro = host.add_macro("MY_HOST_MACRO", 1, "Testing The Host Macro")
        host.add_macro("MY_SECRET_MACRO", "some secret", "Testing The Secrets", MacroType.SECRET)
        host.link_template(template)
        host_item = host.add_item("Item Own", "item.test[own]").add_tag("Service", "Testing Host")
        host_if1 = AgentInterface()
        host.link_interface(host_if1)
        host_item.link_interface(host_if1)
        host.add_trigger(name="Host Simple trigger", expression=functions.aggregate.Min(host_item, 10) > host_macro,
                         priority=TriggerPriority.HIGH, description="A single host item trigger")

        host_graph = host.add_graph("Host Graph")
        host_graph.link_item(host_item, "1A7C11")

        host_trigger_expr = (functions.history.Last(host_item) > host_macro) & (functions.history.Last(host_item) <  host.get_macro("MY_MACRO"))
        host.add_trigger(name="Host Complex trigger", expression=host_trigger_expr,
                         priority=TriggerPriority.WARNING,
                         description="Host trigger using two items")

        super_template = self.add_template("Super Template", groups=[template_group])
        super_template.link_template(template)
        super_template.add_macro("SUPER_TEMPLATE_MACRO", "SUPER TEMPLATE MACRO")

        super_host = self.add_host("Templar Super Host", groups=[host_group])
        super_host.link_template(super_template)
        super_host.link_interface(host_if1)
        super_host_item = super_host.add_item("Super Host Item", "item.test[super]")
        super_host_item.link_interface(host_if1)
        super_host.add_trigger(name="Global Macro Test",
                               expression=functions.aggregate.Min(super_host_item, "10") > super_host.get_macro("TEMPLAR_GLOBAL_MACRO"))
        super_host.add_trigger(name="Global Macro Test 2",
                               expression=functions.aggregate.Min(super_host_item, "10") > super_host.get_macro("MY_MACRO"))


if __name__ == "__main__":
    import yaml

    module = SampleTemplate()
    print(yaml.dump(module.to_export(), default_flow_style=False, sort_keys=False))
