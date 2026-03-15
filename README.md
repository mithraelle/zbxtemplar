# zbxtemplar

A Pythonic framework for programmatic Zabbix configuration generation (Monitoring as Code).

Define templates, hosts, user groups, and users as Python code. Generate Zabbix-native YAML (importable via UI or API) and decree YAML (applied by the executor). The goal is to cover the essential Zabbix configuration primitives — not every possible option. If you need a field that isn't exposed, raw dicts and string expressions give you an escape hatch.

## Installation

```bash
pip install .
```

## Core Architecture

The project follows the `src-layout`:

- `zbxtemplar.zabbix` — Domain models: Template, Host, Item, Trigger, Graph, Dashboard.
- `zbxtemplar.core` — Module contracts (`TemplarModule`, `DecreeModule`) and entity registry (`Context`).
- `zbxtemplar.decree` — Decree domain classes: `DecreeEntity`, `UserGroup`, `User`, `UserMedia`, `Action`, `TriggerAction`, conditions, operations, and predefined constants.
- `zbxtemplar.main` — CLI entry point and module loader.
- `zbxtemplar.executor` — Applies generated artifacts to a live Zabbix instance.

## Module Contract

Configuration is defined as Python classes that inherit from `TemplarModule` (monitoring) or `DecreeModule` (users/groups). The constructor is the contract — all configuration logic lives in `__init__`.

Constructor arguments become CLI parameters via `--param KEY=VALUE`. The loader inspects the `__init__` signature and performs type coercion based on annotations (`str`, `int`, `float`, `bool`).

```python
from zbxtemplar.core import TemplarModule
from zbxtemplar.zabbix import Template, Item, Host, TriggerPriority
from zbxtemplar.zabbix.Template import TemplateGroup
from zbxtemplar.zabbix.Host import HostGroup, AgentInterface

class MyModule(TemplarModule):
    def __init__(self, alert_threshold: int = 90):
        super().__init__()

        template = Template(name="My Service", groups=[TemplateGroup("Custom Templates")])
        template.add_tag("Service", "MyApp")
        template.add_macro("THRESHOLD", alert_threshold, "Alert threshold")

        item = Item("CPU Usage", "system.cpu.util", template.name)
        item.add_trigger("High CPU", "last", ">",
                         template.get_macro("THRESHOLD"),
                         priority=TriggerPriority.HIGH)
        template.add_item(item)

        host = Host("My Server", groups=[HostGroup("Linux Servers")])
        host.add_template(template)
        host.add_interface(AgentInterface(ip="192.168.1.10"))

        self.add_template(template)
        self.add_host(host)
```

The loader discovers all `TemplarModule` and `DecreeModule` subclasses in the file by class name.

### Running standalone

Add a `__main__` guard to run the module directly:

```python
if __name__ == "__main__":
    import yaml
    module = MyModule()
    print(yaml.dump(module.to_export(), default_flow_style=False, sort_keys=False))
```

## CLI

Single command, auto-detects module type:

```bash
# Combined output (templates + hosts)
zbxtemplar module.py -o output.yml

# Separate outputs
zbxtemplar module.py --templates-output templates.yml --hosts-output hosts.yml

# With UUID namespace
zbxtemplar module.py -o output.yml --namespace "My Company"

# With parameters
zbxtemplar module.py -o output.yml --param ENV=prod --param ALERT_THRESHOLD=5

# Decree module with context
zbxtemplar decree_module.py -o decree.yml --context templates.yml --context hosts.yml
```

| Argument | Description |
|---|---|
| `module` | Path to a `.py` file with `TemplarModule`/`DecreeModule` subclass(es) |
| `-o, --output` | Combined output YAML file path |
| `--templates-output` | Output YAML for templates only (TemplarModule) |
| `--hosts-output` | Output YAML for hosts only (TemplarModule) |
| `--user-groups-output` | Output YAML for user groups only (DecreeModule) |
| `--users-output` | Output YAML for users only (DecreeModule) |
| `--actions-output` | Output YAML for actions only (DecreeModule) |
| `--namespace` | UUID namespace for deterministic ID generation |
| `--param KEY=VALUE` | Parameter passed to the module constructor (repeatable) |
| `--context FILE` | Context YAML file for decree validation (repeatable) |

At least one output flag is required.

## Programmatic Loading

```python
from zbxtemplar.main import load_module

modules = load_module("path/to/module.py", params={"ENV": "prod"})
# Returns {"ClassName": <instance>, ...}

for name, mod in modules.items():
    export = mod.to_export()  # Full zabbix_export or decree dict
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
from zbxtemplar.zabbix import Host
from zbxtemplar.zabbix.Host import HostGroup, AgentInterface

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
from zbxtemplar.zabbix.Host import HostGroup

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
from zbxtemplar.zabbix import Dashboard, DashboardPage
from zbxtemplar.zabbix.DashboardWidget import ClassicGraph

page = DashboardPage(name="Overview", display_period=120)
page.add_widget(ClassicGraph(template=template.name, graph=graph, width=36, height=5))

dashboard = Dashboard("My Dashboard", display_period=60, auto_start=YesNo.NO)
dashboard.add_page(page)
template.add_dashboard(dashboard)
```

Widgets are concrete subclasses of `Widget` (abstract). Each widget type lives in `zbxtemplar.zabbix.DashboardWidget`. Creating custom widgets is straightforward — subclass `Widget`, define `type` and `widget_fields()`.

## DecreeModule

Decree modules generate user groups, users, and actions as decree YAML (consumed by the executor).

```python
from zbxtemplar.core import DecreeModule
from zbxtemplar.decree import UserGroup, User, UserMedia, MediaType, UserRole, GuiAccess, Permission, Severity

class MyDecree(DecreeModule):
    def __init__(self, alert_email: str = "alerts@example.com"):
        super().__init__()

        group = UserGroup("Operations", gui_access=GuiAccess.INTERNAL)
        group.add_host_group("Linux servers", Permission.READ)
        group.add_template_group("Custom Templates", Permission.READ_WRITE)
        self.add_user_group(group)

        admin = User("zbx-admin", role=UserRole.SUPER_ADMIN)
        admin.set_password("${ZBX_ADMIN_PASSWORD}")
        admin.add_group(group)

        email = UserMedia(MediaType.EMAIL, alert_email)
        email.set_severity([Severity.AVERAGE, Severity.HIGH, Severity.DISASTER])
        admin.add_media(email)
        self.add_user(admin)
```

Context files provide known names for cross-reference validation:

```bash
zbxtemplar decree_module.py -o decree.yml --context templates.yml --context hosts.yml
```

### Actions

Actions define automated responses to events. Currently supported: `TriggerAction` (eventsource 0).

```python
from zbxtemplar.decree.Action import TriggerAction
from zbxtemplar.decree.action_conditions import (
    HostGroupCondition, SeverityCondition, HostTemplateCondition,
    TagCondition, ConditionList, EvalType,
)

action = TriggerAction("Notify on production problems")

# Conditions — use & (and), | (or), ~ (not) operators
action.set_conditions(
    HostGroupCondition("Production") & SeverityCondition(Severity.HIGH)
)

# Or use a ConditionList for simpler AND/OR/AND_OR evaluation
conditions = ConditionList(EvalType.AND_OR)
conditions.add(HostGroupCondition("Production"))
conditions.add(SeverityCondition(Severity.HIGH))
action.set_conditions(conditions)

# Operations — escalation with send_message
action.operations.send_message(
    groups=["Operations"], step_from=1, step_to=3,
    subject="Problem: {EVENT.NAME}", message="Host: {HOST.NAME}"
)

# Recovery and update operations (no escalation)
action.recovery_operations.send_message(groups=["Operations"])
action.update_operations.send_message(groups=["Operations"])

self.add_action(action)
```

#### Condition expressions

Bare expressions are auto-wrapped into `ConditionExpression` (evaltype 3 with formula):

```python
a = HostGroupCondition("Production")
b = HostGroupCondition("Staging")
c = SeverityCondition(Severity.HIGH)

action.set_conditions((a | b) & c)       # formula: "(A or B) and C"
action.set_conditions(a & ~b)            # formula: "A and not B"
```

Python's `&`, `|`, `~` operator precedence matches Zabbix's `and`, `or`, `not` — parentheses are generated automatically when needed.

**Safety:** Using Python's `and`/`or`/`not` keywords instead of `&`/`|`/`~` raises `TypeError` immediately (conditions override `__bool__`).

#### Available condition types

All 26 Zabbix condition types are supported (conditiontype 0–28). Each has a typed `Op` enum restricting to valid operators only. Common ones:

| Class | conditiontype | Default operator |
|---|---|---|
| `HostGroupCondition` | 0 | EQUALS |
| `HostCondition` | 1 | EQUALS |
| `TriggerCondition` | 2 | EQUALS |
| `EventNameCondition` | 3 | CONTAINS |
| `SeverityCondition` | 4 | GREATER_OR_EQUAL |
| `TriggerValueCondition` | 5 | EQUALS |
| `HostTemplateCondition` | 13 | EQUALS |
| `TagCondition` | 25 | EQUALS |
| `TagValueCondition` | 26 | EQUALS |

All condition classes are in `zbxtemplar.decree.action_conditions`.

## Predefined Constants

Commonly referenced Zabbix objects are available as typed constants with IDE autocomplete:

```python
from zbxtemplar.decree import MediaType, UserRole, GuiAccess, Permission, Severity

MediaType.EMAIL       # "Email"
MediaType.SLACK       # "Slack"
MediaType.PAGERDUTY   # "PagerDuty"
UserRole.SUPER_ADMIN  # "Super admin role"
```

| Class | Values |
|---|---|
| `MediaType` | 41 built-in media types (Zabbix 7.4) |
| `UserRole` | `SUPER_ADMIN`, `ADMIN`, `USER`, `GUEST` |
| `GuiAccess` | `DEFAULT`, `INTERNAL`, `LDAP`, `DISABLED` |
| `Permission` | `NONE`, `READ`, `READ_WRITE` |
| `Severity` | `NOT_CLASSIFIED`, `INFORMATION`, `WARNING`, `AVERAGE`, `HIGH`, `DISASTER` |
| `MacroType` | `TEXT`, `SECRET`, `VAULT` |

Constants are a convenience, not a requirement — plain strings work anywhere a constant is expected.

## Global Configuration

```python
from zbxtemplar.zabbix.ZbxEntity import set_uuid_namespace

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

# Apply state configuration (user groups, users, actions)
zbxtemplar-exec decree state.yml --token $ZBX_TOKEN

# Create service accounts (shorthand — feeds into decree)
zbxtemplar-exec add_user users.yml --token $ZBX_TOKEN
```

Connection credentials can be passed via CLI flags (`--url`, `--token`, `--user`, `--password`) or environment variables (`ZABBIX_URL`, `ZABBIX_TOKEN`, `ZABBIX_USER`, `ZABBIX_PASSWORD`).

### Decree

A decree is zbxtemplar's declarative YAML format for live-state configuration that has no Zabbix-native import format. A single decree file can contain any combination of supported sections, processed in dependency order: `user_group` → `add_user` → `actions`.

```yaml
user_group:
  - name: Templar Users
    gui_access: INTERNAL
    host_groups:
      - name: Linux servers
        permission: READ
    template_groups:
      - name: Custom Templates
        permission: READ_WRITE

add_user:
  - username: zbx-service
    role: Super admin role
    password: ${ZBX_SERVICE_PASSWORD}
    groups:
      - Templar Users

actions:
  - name: Notify on problems
    eventsource: 0
    operations:
      - operationtype: 0
        opmessage_grp:
          - usrgrpid: Templar Users
        esc_step_from: 1
        esc_step_to: 1
        esc_period: 0
    filter:
      evaltype: 3
      formula: A and B
      conditions:
        - conditiontype: 0
          operator: 0
          value: Linux servers
          formulaid: A
        - conditiontype: 4
          operator: 5
          value: HIGH
          formulaid: B
```

All references are by name — the executor resolves IDs at runtime (host groups, templates, user groups, users, media types in conditions and operations). In a scroll, `decree` accepts a file path, an inline dict, or a list mixing both.

Named constants for `gui_access`: `DEFAULT`, `INTERNAL`, `LDAP`, `DISABLED`.
Named constants for `permission`: `NONE`, `READ`, `READ_WRITE`.
Severity uses comma-separated names instead of bitmasks: `NOT_CLASSIFIED`, `INFORMATION`, `WARNING`, `AVERAGE`, `HIGH`, `DISASTER`.

If a user has `token` defined and the token already exists, the executor raises an error. Set `force_token: true` to delete and recreate the token.

The `add_user` CLI command is a shorthand that feeds a file containing `add_user:` into the decree pipeline.

### Scroll

A scroll is a static YAML file describing a full deployment sequence. Stages execute in a fixed pipeline order: `bootstrap` → `templates` → `state`.

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
    apply:
      - templates.yml
      - media-types.yml

  - stage: state
    decree:
      user_group:
        - name: Templar Users
          gui_access: INTERNAL
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

File paths in scroll actions resolve relative to the scroll file's directory, not the working directory. String values may contain `${ENV_VAR}` references, resolved from the OS environment before any API calls. Missing variables cause a pre-flight failure — no partial execution.
