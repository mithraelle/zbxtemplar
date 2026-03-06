# zbxtemplar

A Pythonic framework for programmatic Zabbix Template generation (Monitoring as Code).

The goal is to cover the essential Zabbix configuration primitives — not every possible option. If you need a field that isn't exposed, raw dicts and string expressions give you an escape hatch.

## Installation

```bash
pip install .
```

## Core Architecture

The project follows the `src-layout`:

- `zbxtemplar.entities` — Domain models: Template, Host, Item, Trigger, Graph, Dashboard.
- `zbxtemplar.core` — Module contract (`TemplarModule`), loader, serialization, shared types.
- `zbxtemplar.main` — CLI entry point.

## Module Contract

Templates and hosts are defined as Python classes that inherit from `TemplarModule`.
The constructor is the contract — all configuration logic lives in `__init__`.

```python
from zbxtemplar.core import TemplarModule
from zbxtemplar.entities import Template, Item, Host, TriggerPriority
from zbxtemplar.entities.Template import TemplateGroup
from zbxtemplar.entities.Host import HostGroup, AgentInterface

class MyModule(TemplarModule):
    def __init__(self):
        super().__init__()

        template = Template(name="My Service", groups=[TemplateGroup("Custom Templates")])
        template.add_tag("Service", "MyApp")
        template.add_macro("THRESHOLD", 90, "Alert threshold")

        item = Item("CPU Usage", "system.cpu.util", template.name)
        item.add_trigger("High CPU", "last", ">",
                         template.get_macro("THRESHOLD"),
                         priority=TriggerPriority.HIGH)
        template.add_item(item)

        host = Host("My Server", groups=[HostGroup("Linux Servers")])
        host.add_template(template)
        host.add_interface(AgentInterface(ip="192.168.1.10"))

        self.templates = [template]
        self.hosts = [host]
```

A module file can contain multiple `TemplarModule` subclasses.
The loader discovers all of them by class name.

### Running standalone

Add a `__main__` guard to run the module directly:

```python
if __name__ == "__main__":
    import yaml
    module = MyModule()
    print(yaml.dump(module.to_export(), default_flow_style=False, sort_keys=False))
```

## CLI

```bash
# Combined output (templates + hosts)
zbxtemplar module.py output.yml

# Separate outputs
zbxtemplar module.py --templates-output templates.yml --hosts-output hosts.yml

# Combined + separate
zbxtemplar module.py output.yml --templates-output templates.yml --hosts-output hosts.yml

# With UUID namespace
zbxtemplar module.py output.yml --namespace "My Company"
```

| Argument | Description |
|---|---|
| `module` | Path to a `.py` file with `TemplarModule` subclass(es) |
| `output` | Combined output YAML file path (optional if split outputs are given) |
| `--templates-output` | Output YAML file path for templates only |
| `--hosts-output` | Output YAML file path for hosts only |
| `--namespace` | UUID namespace for deterministic ID generation |

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
template = Template(name="My Template", groups=[TemplateGroup("Custom Group")])
template.add_tag("Service", "MyApp")
template.add_macro("TIMEOUT", 30, "Connection timeout")
template.add_item(item)
```

### Host

```python
from zbxtemplar.entities import Host
from zbxtemplar.entities.Host import HostGroup, AgentInterface

host = Host("My Host", groups=[HostGroup("Linux Servers")])
host.add_tag("Environment", "Production")
host.add_macro("HOST_PORT", 8080, "Application port")

# Link a template
host.add_template(template)

# Add an interface (first interface becomes the default)
iface = AgentInterface(ip="192.168.1.10", port="10050")
host.add_interface(iface)

# Host-level items, triggers, graphs work the same as on templates
item = Item("Host Uptime", "system.uptime", host.name)
item.set_interface(iface)
host.add_item(item)

# Macro lookup walks linked templates when not found on the host
host.get_macro("TEMPLATE_MACRO")  # falls back to template macros
```

Hosts produce UUID-free YAML (matching Zabbix export format). Dashboards are template-only and cannot be added to hosts.

`AgentInterface` is the built-in interface type (`type: ZABBIX`). Custom interface types can be created by subclassing `HostInterface`.

### HostGroup

```python
from zbxtemplar.entities.Host import HostGroup

group = HostGroup("Linux Servers")
```

Works the same as `TemplateGroup` — name-based identity with a deterministic UUID.

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
page.add_widget(ClassicGraph(template=template.name, graph=graph, width=36, height=5))

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

## Executor

The executor is a separate tool that applies generated YAML and other configuration to a live Zabbix instance. Install with the `executor` extra:

```bash
pip install ".[executor]"
```

### Commands

```bash
# Bootstrap or rotate super admin password
zbxtemplar-exec set_super_admin --new-password $ZBX_ADMIN_PASSWORD \
  --user Admin --password zabbix --url http://localhost

# Set global macros
zbxtemplar-exec set_macro SNMP_COMMUNITY public --token $ZBX_TOKEN
zbxtemplar-exec set_macro macros.yml --token $ZBX_TOKEN

# Import Zabbix-native YAML (templates, hosts, media types, etc.)
zbxtemplar-exec apply zabbix-native.yml --token $ZBX_TOKEN

# Apply user groups with permissions
zbxtemplar-exec decree user-groups.yml --token $ZBX_TOKEN

# Create service accounts
zbxtemplar-exec add_user users.yml --token $ZBX_TOKEN
```

Connection credentials can be passed via CLI flags (`--url`, `--token`, `--user`, `--password`) or environment variables (`ZABBIX_URL`, `ZABBIX_TOKEN`, `ZABBIX_USER`, `ZABBIX_PASSWORD`).

### Decree — User Groups

A decree file defines user groups with host/template group permissions. All references are by name — the executor resolves IDs at runtime. See [tests/test_user_group.decree.yml](tests/test_user_group.decree.yml) for a reference example.

Named constants for `gui_access`: `DEFAULT`, `INTERNAL`, `LDAP`, `DISABLED`.
Named constants for `permission`: `NONE`, `READ`, `READ_WRITE`.

### Add User

Creates service accounts and special users. Roles, user groups, and media types are referenced by name. See [tests/test_add_user.yml](tests/test_add_user.yml) for a reference example.

Severity uses comma-separated names instead of bitmasks: `NOT_CLASSIFIED`, `INFORMATION`, `WARNING`, `AVERAGE`, `HIGH`, `DISASTER`.

### Scroll

A scroll is a static YAML file describing a full deployment sequence. Stages execute in a fixed pipeline order: `bootstrap` → `templates` → `state` → `users`.

```yaml
stages:
  - stage: bootstrap
    set_super_admin:
      password: ${ZBX_ADMIN_PASSWORD}
    set_macro:
      - name: SNMP_COMMUNITY
        value: public
      - name: DB_PASSWORD
        value: ${DB_PASSWORD}
        type: secret

  - stage: templates
    apply: zabbix-native.yml

  - stage: state
    decree: user-groups.yml

  - stage: users
    add_user:
      - username: zbx-service
        role: Super admin role
        password: ${ZBX_SERVICE_PASSWORD}
```

```bash
zbxtemplar-exec scroll deploy.scroll.yml --token $ZBX_TOKEN
zbxtemplar-exec scroll deploy.scroll.yml --from-stage state
zbxtemplar-exec scroll deploy.scroll.yml --only-stage bootstrap
```

String values may contain `${ENV_VAR}` references, resolved from the OS environment before any API calls. Missing variables cause a pre-flight failure — no partial execution.
