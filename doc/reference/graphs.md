# Graphs (Classic / Template-level)

Template and host graph objects rendered in the Zabbix UI.
Not to be confused with dashboard SVG graph widgets (see `dashboards.md`).

## Imports

```python
from zbxtemplar.zabbix.Graph import GraphType, YAxisType, DrawType, CalcFnc, GraphItemType, YAxisSide
from zbxtemplar.zabbix.ZbxEntity import YesNo
```

## Graph

```python
graph = template.add_graph(
    name="CPU load",
    type=GraphType.NORMAL,             # NORMAL, STACKED, PIE, EXPLODED
    show_triggers=YesNo.YES,           # overlay trigger threshold lines; YesNo.YES or NO
    show_legend=YesNo.YES,
    y_min_type=YAxisType.CALCULATED,   # CALCULATED (auto), FIXED, ITEM
    y_max_type=YAxisType.FIXED,
    y_min=None,                        # number/string when FIXED; Item when ITEM
    y_max=100,
)
# or host.add_graph(...)
```

When `y_min_type` or `y_max_type` is `ITEM`, pass the corresponding `Item` object
directly as `y_min` / `y_max`. The item must belong to the same template or host, or to a
template linked to it.

## Linking items to a graph

```python
graph.link_item(
    item,
    color="1A7C11",                       # hex color, no #
    order=0,                              # display order (lower = drawn first)
    drawtype=DrawType.SINGLE_LINE,        # SINGLE_LINE, FILLED_REGION, BOLD_LINE,
                                          # DOTTED_LINE, DASHED_LINE, GRADIENT_LINE
    calc_fnc=CalcFnc.AVG,                # MIN, AVG, MAX, ALL, LAST
    type=GraphItemType.SIMPLE,            # SIMPLE, GRAPH_SUM (pie/exploded sum item)
    yaxisside=YAxisSide.LEFT,             # LEFT, RIGHT
)
```

`GRAPH_SUM` marks the item as the "sum" reference in PIE / EXPLODED graphs.

Items of linked templates can be used directly: the graph belongs to the template or host it
was added to, so an umbrella template can combine items from several linked templates in one graph.