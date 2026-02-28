# zbxtemplar

A Pythonic framework for programmatic Zabbix Template generation (Monitoring as Code).

The goal is to cover the essential Zabbix configuration primitives — not every possible option. If you need a field that isn't exposed, raw dicts and string expressions give you an escape hatch.

## Installation

```bash
pip install .
```

## Core Architecture

The project follows the `src-layout`:

- `zbxtemplar.entities` — Domain models: Template, Item, Trigger, Graph, Dashboard.
- `zbxtemplar.core` — Module contract (`TemplarModule`), loader, serialization, shared types.
- `zbxtemplar.main` — CLI entry point.

## Module Contract

Templates are defined as Python classes that inherit from `TemplarModule`.
The constructor is the contract — all template logic lives in `__init__`.

```python
from zbxtemplar.core import TemplarModule
from zbxtemplar.entities import Template, Item, Trigger, TriggerPriority, Graph

class MyTemplate(TemplarModule):
    def __init__(self):
        super().__init__()

        template = Template(name="My Service")
        template.add_tag("Service", "MyApp")
        template.add_macro("THRESHOLD", 90, "Alert threshold")

        item = Item("CPU Usage", "system.cpu.util")
        item.add_trigger("High CPU", "last", ">",
                         template.get_macro("THRESHOLD"),
                         priority=TriggerPriority.HIGH)
        template.add_item(item)

        self.templates = [template]
        self.triggers = []
        self.graphs = []
```

A module file can contain multiple `TemplarModule` subclasses.
The loader discovers all of them by class name.

### Running standalone

Add a `__main__` guard to run the module directly:

```python
if __name__ == "__main__":
    import yaml
    module = MyTemplate()
    print(yaml.dump(module.to_export(), default_flow_style=False, sort_keys=False))
```

## CLI

```bash
# Basic usage
zbxtemplar module.py output.yml
python -m zbxtemplar module.py output.yml

# With options
zbxtemplar module.py output.yml \
    --namespace "My Company" \
    --template-group "Custom Templates"
```

| Argument | Description |
|---|---|
| `module` | Path to a `.py` file with `TemplarModule` subclass(es) |
| `output` | Output YAML file path |
| `--namespace` | UUID namespace for deterministic ID generation |
| `--template-group` | Default template group name |

## Programmatic Loading

```python
from zbxtemplar.core import load_module

modules = load_module("path/to/module.py")
# Returns {"ClassName": <instance>, ...}

for name, mod in modules.items():
    export = mod.to_export()  # Full zabbix_export dict
```

## Entities Reference

### Template

```python
template = Template(name="My Template", groups=["Custom Group"])
template.add_tag("Service", "MyApp")
template.add_macro("TIMEOUT", 30, "Connection timeout")
template.add_item(item)
```

### Item

```python
item = Item("CPU Usage", "system.cpu.util")

# Expression helper — builds Zabbix function strings
item.expr("last")            # last(/host/key)
item.expr("min", "10m")      # min(/host/key,10m)
item.expr("count", "#10")    # count(/host/key,#10)

# Single-item trigger shorthand
item.add_trigger("High CPU", "last", ">", 90,
                 priority=TriggerPriority.HIGH,
                 description="CPU threshold exceeded")

# With function args
item.add_trigger("Sustained high", "min", ">", 100,
                 fn_args=("10m",), priority=TriggerPriority.WARNING)
```

All enum values (`ItemType`, `ValueType`, `TriggerPriority`, `GraphType`, `DrawType`, `CalcFnc`, etc.) follow the Zabbix export format documentation.

### Trigger

```python
# Standalone (multi-item) trigger — raw expression string
Trigger(name="Complex alert",
        expression=item1.expr("last") + ">0 and " + item2.expr("min", "5m") + "<100",
        priority=TriggerPriority.WARNING,
        description="Multi-item condition")
```

### Macro

Macros work seamlessly in string contexts:

```python
template.add_macro("MY_MACRO", 1, "Description")
macro = template.get_macro("MY_MACRO")

str(macro)                    # {$MY_MACRO}
item.expr("last") + ">" + macro  # last(/host/key)>{$MY_MACRO}
item.add_trigger("Alert", "last", ">", macro)  # works as threshold
```

### Graph

```python
graph = Graph("CPU Graph",
              graph_type=GraphType.STACKED,
              y_min_type=YAxisType.FIXED, y_min=0,
              y_max_type=YAxisType.FIXED, y_max=100)

graph.add_item(item1, "FF0000")
graph.add_item(item2, "00FF00",
               drawtype=DrawType.BOLD_LINE,
               calc_fnc=CalcFnc.MAX,
               yaxisside=YAxisSide.RIGHT)
```

### Dashboard

```python
from zbxtemplar.entities import Dashboard, DashboardPage
from zbxtemplar.entities.DashboardWidget import ClassicGraph

page = DashboardPage(name="Overview", display_period=120)
page.add_widget(ClassicGraph(host=template.name, graph=graph, width=36, height=5))

dashboard = Dashboard("My Dashboard", display_period=60, auto_start=YesNo.NO)
dashboard.add_page(page)
template.add_dashboard(dashboard)
```

Widgets are concrete subclasses of `Widget` (abstract). Each widget type lives in `zbxtemplar.entities.DashboardWidget`. Creating custom widgets is straightforward — subclass `Widget`, define `type` and `widget_fields()`.

## Global Configuration

```python
from zbxtemplar.core.ZbxEntity import set_uuid_namespace

set_uuid_namespace("My Company")  # Deterministic UUIDs scoped to namespace
```