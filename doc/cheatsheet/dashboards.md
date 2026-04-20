# Dashboards & Widgets

## Imports

```python
from zbxtemplar.zabbix.Dashboard import Dashboard, DashboardPage
from zbxtemplar.zabbix.ZbxEntity import YesNo
from zbxtemplar.zabbix.DashboardWidget.ClassicGraph import ClassicGraph
from zbxtemplar.zabbix.DashboardWidget.SimpleGraph import SimpleGraph
from zbxtemplar.zabbix.DashboardWidget.ItemHistory import ItemHistory, ItemHistoryHeader
from zbxtemplar.zabbix.DashboardWidget import Graph as dashGraph
```

## Dashboard & pages

```python
dashboard = Dashboard(name="My Dashboard", display_period=30, auto_start=YesNo.YES)
# auto_start / display_period apply to the whole dashboard
# YesNo: YES, NO

page = DashboardPage(name="Overview", display_period=120)
# name is optional for the first page; display_period overrides dashboard default for this page
dashboard.add_page(page)
template.add_dashboard(dashboard)
```

## Widget layout

All widgets accept `x`, `y`, `width`, `height` (grid units). The dashboard grid is 72 columns wide.

## ClassicGraph

Displays a template/host `Graph` object (from `graphs.md`).

```python
w = ClassicGraph(template=template.name, graph=graph, x=0, y=0, width=36, height=5)
page.add_widget(w)
```

## SimpleGraph

Single-item graph — no separate `Graph` object needed.

```python
w = SimpleGraph(item=item, x=0, y=0, width=36, height=5, name="CPU load")
page.add_widget(w)
```

## ItemHistory

Scrollable table of recent item values.

```python
w = ItemHistory(x=0, y=0, width=18, height=5)
w.add_item(item1, "Column header")  # empty string uses item name
w.add_item(item2, "")
w.show_timestamp(True)
w.show_column_header(ItemHistoryHeader.HORIZONTAL)  # NO, HORIZONTAL, VERTICAL
page.add_widget(w)
```

## SVG Graph widget (dashGraph.Graph)

Flexible dashboard-only graph composed of data sets.

```python
g = dashGraph.Graph(name="Trends", x=0, y=0, width=36, height=8)
```

### Data sets

**ItemListSet** — explicit list of items:

```python
ds = dashGraph.ItemListSet(label="My Items")
ds.add_item(item1, "1A7C11")   # hex color, no #
ds.add_item(item2, "274482")
```

**ItemPatternSet** — wildcard key matching; specify either `color` or `palette` (not both):

```python
ds = dashGraph.ItemPatternSet(label="CPU items", palette=3)   # palette: 0–11
ds = dashGraph.ItemPatternSet(label="CPU items", color="1A7C11")
ds.add_pattern("cpu")
ds.add_pattern("system.cpu*")
```

### Draw style (set on data set)

```python
ds.set_draw_style(dashGraph.Line(stacked=False, width=1, transparency=5, fill=3,
                                  missed_data=dashGraph.MissedData.NONE))
ds.set_draw_style(dashGraph.Bar(stacked=False, transparency=5))
ds.set_draw_style(dashGraph.Points(point_size=1, transparency=5))
ds.set_draw_style(dashGraph.Staircase(stacked=False, width=1, transparency=5, fill=3,
                                       missed_data=dashGraph.MissedData.NONE))
# MissedData: NONE, CONNECTED, TREAT_AS_0, LAST_KNOWN
# width: 1–10, transparency: 0–10, fill: 0–10
```

### Data set options

```python
ds.set_Y_axis(dashGraph.YAxis.LEFT)      # LEFT, RIGHT
ds.set_aggregate(
    dashGraph.AggregateFunc.AVG,          # NO, MIN, MAX, AVG, COUNT, SUM, FIRST, LAST
    interval="1h",
    aggregate_by=dashGraph.AggregateBy.EACH_ITEM,  # EACH_ITEM, DATA_SET
)
```

### Graph options

```python
g.add_data_set(ds)

g.set_display_options(
    source=dashGraph.DataSource.AUTO,     # AUTO, HISTORY, TRENDS
    triggers=False,
    working_time=False,
    percentline_left=95,   # optional; enables left percentile line at given value
    percentline_right=None,
)

g.set_legend(
    show_stats=True,
    show_aggregation=True,
    variable_legend_lines=True,
    legend_lines=4,         # 1–10
    legend_columns=2,       # 1–4
)

page.add_widget(g)
```