# Actions, Conditions & Operations

`self.add_*_action()` calls are `DecreeModule` methods called from inside `compose()`.

## Imports

```python
from zbxtemplar.decree.action_conditions import (
    EvalType, ConditionList,
    HostGroupCondition, HostCondition, HostTemplateCondition,
    SeverityCondition, TriggerValueCondition, EventNameCondition,
    TimePeriodCondition, SuppressedCondition,
    TagCondition, TagValueCondition,
    HostNameCondition, HostMetadataCondition, ProxyCondition,
    DiscoveryStatusCondition, DiscoveryRuleCondition, DiscoveryCheckCondition,
    DiscoveryObjectCondition, DiscoveredServiceTypeCondition, DiscoveredServicePortCondition,
    HostIPCondition, UptimeCondition, ReceivedValueCondition,
    EventTypeCondition, ServiceCondition, ServiceNameCondition,
)
from zbxtemplar.decree import Severity
```

## Action types

```python
action = self.add_trigger_action("Alert on production")
action = self.add_autoregistration_action("Auto-register linux hosts")
```

## Conditions — flat list

```python
cl = ConditionList(EvalType.AND_OR)   # EvalType: AND_OR, AND, OR
# AND_OR: same-type conditions are OR'd, groups are AND'd
cl.add(HostGroupCondition("Production"))
cl.add(HostGroupCondition("Staging"))    # OR'd with Production
cl.add(SeverityCondition(Severity.HIGH)) # AND'd with host group block
action.set_conditions(cl)
```

## Conditions — expression tree

Use `&`, `|`, `~` — Python `and`/`or`/`not` keywords raise `TypeError`.

```python
a = HostGroupCondition(self.context.get_host_group("Production"))
b = HostTemplateCondition(self.context.get_template("Linux"))
c = SeverityCondition(Severity.HIGH)
action.set_conditions((a | b) & c)   # auto-wrapped into ConditionExpression
```

## Condition types

| Class | conditiontype | Default op | Available ops |
|---|---|---|---|
| HostGroupCondition | 0 | EQUALS | EQUALS, NOT_EQUALS |
| HostCondition | 1 | EQUALS | EQUALS, NOT_EQUALS |
| TriggerCondition | 2 | EQUALS | EQUALS, NOT_EQUALS |
| EventNameCondition | 3 | CONTAINS | CONTAINS, NOT_CONTAINS |
| SeverityCondition | 4 | GREATER_OR_EQUAL | EQUALS, NOT_EQUALS, GREATER_OR_EQUAL, LESS_OR_EQUAL |
| TriggerValueCondition | 5 | EQUALS | EQUALS |
| TimePeriodCondition | 6 | IN | IN, NOT_IN |
| HostIPCondition | 7 | EQUALS | EQUALS, NOT_EQUALS |
| DiscoveredServiceTypeCondition | 8 | EQUALS | EQUALS, NOT_EQUALS |
| DiscoveredServicePortCondition | 9 | EQUALS | EQUALS, NOT_EQUALS |
| DiscoveryStatusCondition | 10 | EQUALS | EQUALS |
| UptimeCondition | 11 | GREATER_OR_EQUAL | GREATER_OR_EQUAL, LESS_OR_EQUAL |
| ReceivedValueCondition | 12 | EQUALS | EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS, GREATER_OR_EQUAL, LESS_OR_EQUAL |
| HostTemplateCondition | 13 | EQUALS | EQUALS, NOT_EQUALS |
| SuppressedCondition | 16 | NO | YES, NO |
| DiscoveryRuleCondition | 18 | EQUALS | EQUALS, NOT_EQUALS |
| DiscoveryCheckCondition | 19 | EQUALS | EQUALS, NOT_EQUALS |
| ProxyCondition | 20 | EQUALS | EQUALS, NOT_EQUALS |
| DiscoveryObjectCondition | 21 | EQUALS | EQUALS |
| HostNameCondition | 22 | CONTAINS | CONTAINS, NOT_CONTAINS, MATCHES, NOT_MATCHES |
| EventTypeCondition | 23 | EQUALS | EQUALS |
| HostMetadataCondition | 24 | CONTAINS | CONTAINS, NOT_CONTAINS, MATCHES, NOT_MATCHES |
| TagCondition | 25 | EQUALS | EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS |
| TagValueCondition | 26 | EQUALS | EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS |
| ServiceCondition | 27 | EQUALS | EQUALS, NOT_EQUALS |
| ServiceNameCondition | 28 | EQUALS | EQUALS, NOT_EQUALS |

Value constants on condition classes:
- `TriggerValueCondition`: `.OK`, `.PROBLEM`
- `DiscoveryStatusCondition`: `"UP"`, `"DOWN"`, `"DISCOVERED"`, `"LOST"`
- `DiscoveryObjectCondition`: `"HOST"`, `"SERVICE"`
- `EventTypeCondition`: `"ITEM_NOT_SUPPORTED"`, `"ITEM_NORMAL"`, `"LLD_NOT_SUPPORTED"`, `"LLD_NORMAL"`, `"TRIGGER_UNKNOWN"`, `"TRIGGER_NORMAL"`

Override op via the class's `.Op` enum:
```python
SeverityCondition(Severity.WARNING, SeverityCondition.Op.GREATER_OR_EQUAL)
HostNameCondition("prod-", HostNameCondition.Op.MATCHES)
TagValueCondition("env", "prod", TagValueCondition.Op.NOT_EQUALS)
```

## Operations — TriggerAction

`action.operations` fires when the problem opens (`TriggerOperations`).
`action.recovery_operations` and `action.update_operations` fire on resolve/ack (`TriggerAckOperations`).

```python
action.operations.send_message(
    groups=[ops_group],           # UserGroup objects or name strings
    users=[alice],                # User objects or username strings
    media_type=MediaType.EMAIL,   # None = all enabled media for the user
    subject="Problem: {EVENT.NAME}",
    message="{EVENT.NAME} on {HOST.NAME}",
    step_from=1,                  # escalation step range (TriggerOperations only)
    step_to=1,
    step_duration=0,              # 0 = use action default
)

action.recovery_operations.send_message(groups=[ops_group], message="Resolved")
action.update_operations.send_message(groups=[ops_group], message="Acknowledged")
```

Action-level timing (TriggerAction only):

```python
action.set_operation_step(duration=3600)  # default escalation step duration, seconds
action.set_pause_suppressed()  # pause while host is in maintenance
action.set_pause_symptoms()  # pause symptom problem notifications
action.set_notify_if_canceled()
```

## Operations — AutoregistrationAction

```python
from zbxtemplar.decree.action_operations import SetInventoryModeOperation

action.operations.add_host()
action.operations.add_to_group("Linux servers")     # name or HostGroup object
action.operations.link_template("Linux Template")   # name or Template object
action.operations.enable_host()
action.operations.disable_host()
action.operations.set_inventory_mode(SetInventoryModeOperation.AUTOMATIC)   # MANUAL or AUTOMATIC
```