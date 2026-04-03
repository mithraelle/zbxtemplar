# Actions Guide

## Scope

The decree action model covers the most complex part of live Zabbix state: alert filters and operations.

Today the codebase exposes two action classes:

- `TriggerAction`
- `AutoregistrationAction`

## Conditions

Conditions live in `zbxtemplar.decree.action_conditions`.

There are two authoring styles.

### `ConditionList`

Use this when Zabbix should handle grouping according to `evaltype`:

```python
from zbxtemplar.decree.action_conditions import ConditionList, EvalType
from zbxtemplar.decree.action_conditions import HostGroupCondition, SeverityCondition

conditions = ConditionList(EvalType.AND_OR)
conditions.add(HostGroupCondition("Production"))
conditions.add(HostGroupCondition("Staging"))
conditions.add(SeverityCondition("HIGH"))
```

### Expression Trees

Use `&`, `|`, and `~` for formula-style logic:

```python
from zbxtemplar.decree.action_conditions import HostGroupCondition, SeverityCondition

prod = HostGroupCondition("Production")
stage = HostGroupCondition("Staging")
high = SeverityCondition("HIGH")

expr = (prod | stage) & high
```

`ConditionExpr.__bool__()` raises a `TypeError`, which means Python `and` and `or` are rejected on purpose. Use `&`, `|`, and `~` instead.

## Trigger Actions

`TriggerAction` supports:

- main operations
- recovery operations
- update operations

Example:

```python
from zbxtemplar.decree.Action import TriggerAction
from zbxtemplar.decree.action_conditions import HostGroupCondition, SeverityCondition

action = TriggerAction("Notify production incidents")
action.set_conditions(HostGroupCondition("Production") & SeverityCondition("HIGH"))

action.operations.send_message(
    groups=["Operations"],
    media_type="Email",
    subject="Production incident",
    message="Problem detected",
    step_from=1,
    step_to=3,
    step_duration=60,
)

action.recovery_operations.send_message(groups=["Operations"])
action.update_operations.send_message(groups=["Operations"])
```

## Autoregistration Actions

`AutoregistrationAction` supports a smaller operation set aimed at newly discovered hosts.

Example:

```python
from zbxtemplar.decree.Action import AutoregistrationAction
from zbxtemplar.decree.action_conditions import HostMetadataCondition

action = AutoregistrationAction("Register linux hosts")
action.set_conditions(HostMetadataCondition("linux"))
action.operations.add_host()
action.operations.add_to_group("Linux Servers")
action.operations.link_template("Template OS Linux")
action.operations.enable_host()
```

## Supported Operations Today

Implemented in code today:

- trigger send-message operations
- trigger recovery send-message operations
- trigger update send-message operations
- autoregistration send-message operations
- autoregistration add-host
- autoregistration add-to-group
- autoregistration link-template
- autoregistration enable-host
- autoregistration disable-host
- autoregistration set-inventory-mode

Not yet implemented as first-class code paths:

- discovery actions
- internal actions
- remote command operations
- the broader trigger host-management operation set described in the design notes

## Practical Advice

- Keep decree action definitions readable; name-based references are a feature.
- Use context files during generation when your action references templates, groups, or other generated objects.
- Start with send-message operations first; they are the most complete path today.
- Treat the root design-note files as roadmap material when you need to understand what is planned beyond the current implementation surface.
