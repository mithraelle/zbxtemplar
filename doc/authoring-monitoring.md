# Authoring Monitoring

This is the narrative guide for composing a `TemplarModule` — templates, hosts, items, triggers, value maps, inventory, and the trigger-expression DSL.

For the compact lookup version, see the reference pages: [`templates_hosts.md`](./reference/templates_hosts.md), [`items_triggers.md`](./reference/items_triggers.md), [`trigger_functions_glossary.md`](./reference/trigger_functions_glossary.md).

For CLI flags, `--param`, `--context`, and macro resolution details see [CLI Reference](./cli-reference.md).

## Why Monitoring Needs Code

The Zabbix UI is fine for a handful of hosts. The problem starts when monitoring becomes combinatorial:

- **Repetition at scale** — one application, a dozen regions, each region with a set of queues, each queue with four items and two triggers. That is a loop in Python. In the UI, it is a thousand clicks.
- **Review** — "you raised the CPU threshold from 80 to 90 last Tuesday — why?" Trivial with `git blame`. Impossible with a Zabbix audit log.
- **Reproducibility** — the same template on dev, staging, and prod. Miss one trigger on prod and the alert goes silent exactly when it matters.
- **Expressions written by hand are fragile** — `{hostname:item.key.avg(5m)}>90` is a string. Typos, wrong key, forgotten escape, missing brace — all accepted silently by the UI and surface as a trigger that never fires. `functions.aggregate.Avg(item, "5m") > 90` is a Python expression. The item reference is a typed object; the operator is type-checked; the `/host/key` path is rendered for you.

## The Shape of a TemplarModule

```python
from zbxtemplar.modules import TemplarModule
from zbxtemplar.zabbix import TriggerPriority, InventoryMode, TemplateGroup, HostGroup, AgentInterface
from zbxtemplar.catalog.zabbix_7_4 import functions, InventoryField


class MyModule(TemplarModule):
    def compose(self, alert_threshold: int = 90):

        template = self.add_template(
            name="My Service",
            groups=[TemplateGroup("Custom Templates")],
        )
        threshold = template.add_macro("THRESHOLD", alert_threshold, "Alert threshold")

        cpu = template.add_item("CPU Usage", "system.cpu.util")
        template.add_trigger(
            name="High CPU",
            expression=functions.history.Last(cpu) > threshold,
            priority=TriggerPriority.HIGH,
        )

        host = self.add_host("my-server", groups=[HostGroup("Linux Servers")])
        host.link_template(template)
        host.link_interface(AgentInterface(ip="192.168.1.10"))
```

`compose()` is the module contract. Its signature becomes the `--param` surface on the CLI. Everything else is helper calls on `self`, the returned `Template`, and the returned `Host`.

## Templates, Hosts, Groups

```python
tg = TemplateGroup("My Templates")
hg = HostGroup("My Hosts")

template = self.add_template("My Template", groups=[tg])
template.add_tag("Service", "monitoring")

host = self.add_host("my-host", groups=[hg])
host.add_tag("env", "prod")
host.link_template(template)
```

Both `add_template` and `add_host` raise `ValueError` on duplicate name within the same module. Groups referenced anywhere in the module are deduplicated automatically during export.

### Linking templates

```python
template.link_template(other_template)
```

Linked templates contribute their macros to the resolution chain below.

### Macros

`get_macro(name)` walks a fixed resolution chain, in order:

1. **Entity macros** — `template.add_macro(...)` or `host.add_macro(...)`
2. **Linked template macros** — macros on templates linked to the current entity
3. **Module macros** — `self.add_macro(...)` inside `compose()`, the "global" tier
4. **Context macros** — global macros loaded from `--context` files

A `KeyError` is raised if the name is not found at any level.

```python
template.add_macro("MY_MACRO", "value", "description")
template.add_macro("DB_PASSWORD", "${DB_PASSWORD}", "DB password", MacroType.SECRET_TEXT)
```

`MacroType` values: `TEXT` (default), `SECRET_TEXT` (alias: `SECRET`), `VAULT`. See [Security & Safety — Global Macro Types](./security.md#global-macro-types) for what each storage type means at the Zabbix end.

`add_macro()` returns the `Macro` object, so you can capture it inline and pass it straight into the expression builder — no separate lookup needed:

```python
threshold = self.add_macro("THRESHOLD", 90, "Alert threshold")
template.add_trigger(
    name="High CPU",
    expression=functions.history.Last(item) > threshold,
    priority=TriggerPriority.HIGH,
)
```

Inside expressions and field values, reference macros by name; `{$MY_MACRO}` and `MY_MACRO` are equivalent.

## Items

```python
from zbxtemplar.zabbix.Item import ItemType, ValueType

item = template.add_item(
    name="CPU load",
    key="system.cpu.load[,avg1]",
    type=ItemType.ZABBIX_PASSIVE,
    value_type=ValueType.FLOAT,
    history="90d",
    trends="365d",
)
item.add_tag("Service", "monitoring")
```

Hosts expose the same `host.add_item(...)` API.

**Item types:** `ZABBIX_PASSIVE`, `ZABBIX_ACTIVE`, `TRAP`, `SIMPLE`, `INTERNAL`, `EXTERNAL`, `ODBC`, `IPMI`, `SSH`, `TELNET`, `CALCULATED`, `JMX`, `SNMP_TRAP`, `SNMP_AGENT`, `DEPENDENT`, `HTTP_AGENT`, `ITEM_TYPE_SCRIPT`, `ITEM_TYPE_BROWSER`.

**Value types:** `UNSIGNED` (default), `FLOAT`, `CHAR`, `LOG`, `TEXT`, `BINARY`.

### Value maps

```python
from zbxtemplar.zabbix.Template import ValueMapType

vm = template.add_value_map("Status Map")
vm.add_mapping("1", "UP", ValueMapType.EQUAL)
vm.add_mapping("0", "DOWN", ValueMapType.EQUAL)

item.link_value_map(vm)
```

## Triggers and the Expression Builder

A trigger is a `name`, a Python `expression`, and a `priority`:

```python
template.add_trigger(
    name="High CPU",
    expression=functions.history.Last(cpu_item) > 90,
    priority=TriggerPriority.HIGH,
)
```

`TriggerPriority`: `NOT_CLASSIFIED`, `INFO`, `WARNING`, `AVERAGE`, `HIGH`, `DISASTER`.

### How the expression builder works

Every trigger function is a typed wrapper class under `zbxtemplar.catalog.zabbix_7_4.functions`. Wrappers take an `Item` object (not a key string) and produce an expression node. Nodes combine through normal Python operators:

```python
functions.history.Last(item)          # last(/Template/key)
functions.aggregate.Avg(item, "5m")   # avg(/Template/key,5m)
functions.aggregate.Min(item, "10m")  # min(/Template/key,10m)
```

Use `==`, `!=`, `>`, `>=`, `<`, `<=` for comparisons, arithmetic operators for math, and `&`, `|`, `~` for Zabbix `and`, `or`, `not`:

```python
expr = functions.aggregate.Avg(cpu, "5m") > 90
expr = functions.history.Last(cpu) > threshold_macro       # renders as {$THRESHOLD}
expr = ((functions.history.Last(cpu) > threshold)
        & (functions.history.Last(mem) < 80))
expr = ~(functions.history.Last(cpu) == 0)                 # renders: not (last(...) = 0)
expr = functions.history.Last(cpu) != 0                    # renders: last(...) <> 0
```

The `/{host}/{key}` path is generated automatically from the item's owner — no string assembly, no escaping, no manual host-name substitution.

### Why `&`/`|`/`~` and not `and`/`or`/`not`

Python's `and`/`or`/`not` are short-circuit boolean operators that call `__bool__` on their operands. A trigger expression is not a boolean — it is a symbolic tree that renders to a string later. zbxtemplar raises a clear `TypeError` if you write `a and b`, so the mistake surfaces at module-load time, not as a silently broken trigger.

### Single-item vs. multi-item triggers

Triggers whose expression references exactly one item are attached under that item in the Zabbix export. Triggers that reference two or more items stay on the owning template or host:

```python
expr = ((functions.history.Last(cpu) > 100)
        & (functions.history.Last(mem) < 0))
trigger = template.add_trigger(
    name="CPU high and memory low",
    expression=expr,
    priority=TriggerPriority.WARNING,
)
trigger.add_tag("scope", "availability")
```

See [trigger_functions_glossary.md](./reference/trigger_functions_glossary.md) for every wrapper (aggregate, history, prediction, bitwise, string, math, etc.).

## Host Inventory

Zabbix host inventory is a fixed set of ~70 asset-tracking fields (OS, hardware, location, contact). Fields can be populated manually, or automatically from item values when the host is in `AUTOMATIC` mode.

```python
from zbxtemplar.zabbix import InventoryMode
from zbxtemplar.catalog.zabbix_7_4 import InventoryField

host.set_inventory_mode(InventoryMode.AUTOMATIC)
host.set_inventory(InventoryField.LOCATION, "DC1 Rack 12")

os_item = template.add_item("OS version", "system.sw.os")
os_item.set_inventory_link(InventoryField.OS)   # populated automatically
```

`InventoryMode`: `DISABLED`, `MANUAL`, `AUTOMATIC`.

Two incoherent combinations raise `ValueError` at generation time (Zabbix would silently drop them on import):

- `inventory` fields set but `inventory_mode` not set
- `inventory` fields set together with `InventoryMode.DISABLED`

`set_inventory_link` on an item is *not* validated against the host mode — Zabbix harmlessly ignores the link in `MANUAL` or `DISABLED` mode, and the same template is meant to be reused across hosts of different modes.

## Graphs and Dashboards

Classic (template-level) graphs and dashboard widgets have their own surface. For the compact references:

- [`graphs.md`](./reference/graphs.md)
- [`dashboards.md`](./reference/dashboards.md)

## Validating Against Existing State

`--context` loads previously generated or exported YAML and exposes it as `self.context` inside `compose()`. Typed lookups raise `ValueError` on a missing name:

```python
class MyMonitoring(TemplarModule):
    def compose(self):
        prod = self.context.get_host_group("Production")     # HostGroup
        web = self.context.get_template("Web Server")        # Template, with items/triggers
```

A typo like `get_host_group("Prodction")` fails at generation time, before any YAML is written. See [CLI Reference — Context Files](./cli-reference.md#context-files) for the full format list and semantics.

## Output

`zbxtemplar my_module.py -o monitoring.yml` writes one combined `zabbix_export` file. To split lifecycles:

```bash
zbxtemplar my_module.py \
  --templates-output templates.yml \
  --hosts-output hosts.yml
```

Module-level macros (defined via `self.add_macro(...)`) require `--macros-output` because Zabbix has no native import format for global macros; the executor applies them through `usermacro.createglobal` / `usermacro.updateglobal`.

## Practical Advice

- Keep module logic inside `compose()`. That is the supported authoring contract; the class constructor is not.
- Prefer typed objects (`Item`, `Macro`, `HostGroup`) over raw name strings. Raw strings are an escape hatch, not the default path.
- Return values from builders (`add_template`, `add_item`, `add_macro`) are meant to be captured and reused in the expression builder and trigger definitions.
- When your module references objects from another module's output (shared host groups, templates), load that output through `--context` so typos fail at generation time.
