# Actions Guide

## Why Actions Need Code

The Zabbix UI handles actions well enough for one-off setup. The problem starts at scale:

- **Reproduction** — the same action across dev, staging, and prod means clicking through the same form three times. Miss one condition checkbox on the third instance and the alert does not fire when it matters.
- **Review** — "you removed the severity condition from the production alert — was that intentional?" Impossible to answer from the Zabbix audit log. Trivial with a git diff.
- **Drift** — someone tweaks the action in the UI. With code-driven config, the next apply restores the declared state.
- **Scale** — "for each team, create a trigger action scoped to that team's host group." In the UI, that is N manual repetitions. In Python, that is a loop.

When the UI stops scaling, the Zabbix API is the only automation path. And the API is where the complexity lives.

### What the API looks like

Creating "notify Ops when production servers are critical" requires raw numeric codes, manual label assignment, and pre-fetched IDs:

```json
{
    "eventsource": 0,
    "name": "Notify production incidents",
    "esc_period": "60",
    "filter": {
        "evaltype": 3,
        "formula": "A and B",
        "conditions": [
            {"conditiontype": 0, "operator": 0, "value": "42", "formulaid": "A"},
            {"conditiontype": 4, "operator": 5, "value": "4", "formulaid": "B"}
        ]
    },
    "operations": [
        {
            "operationtype": 0,
            "opmessage": {"mediatypeid": "3", "default_msg": 0,
                          "subject": "Production incident",
                          "message": "Problem detected"},
            "opmessage_grp": [{"usrgrpid": "8"}],
            "esc_step_from": 1, "esc_step_to": 3, "esc_period": "60"
        }
    ],
    "recovery_operations": [
        {"operationtype": 11, "opmessage": {},
         "opmessage_grp": [{"usrgrpid": "8"}]}
    ]
}
```

`"42"` is a host group ID. `"4"` is severity HIGH. `"3"` is the Email media type ID. `"8"` is the Operations user group ID. Each had to be looked up with separate API calls.

### The same action in zbxtemplar

```python
action = TriggerAction("Notify production incidents")
action.set_conditions(
    HostGroupCondition("Production") & SeverityCondition("HIGH")
)

action.operations.send_message(
    groups=["Operations"],
    media_type="Email",
    subject="Production incident",
    message="Problem detected",
    step_from=1, step_to=3, step_duration=60,
)
action.recovery_operations.send_message(groups=["Operations"])
```

Names instead of IDs. Words instead of numbers. Invalid combinations prevented by the type system.

---

## Conditions

Conditions live in `zbxtemplar.decree.action_conditions`.

### Typed Conditions With Scoped Operators

Each condition class exposes only its valid operators through a nested `Op` enum. Use an invalid operator and you get a type error, not a silently broken condition.

```python
SeverityCondition("HIGH", SeverityCondition.Op.GREATER_OR_EQUAL)
```

`SeverityCondition.Op` contains `EQUALS`, `NOT_EQUALS`, `GREATER_OR_EQUAL`, `LESS_OR_EQUAL`. There is no `CONTAINS` — because Zabbix does not support it for severity conditions.

All 26 Zabbix condition types are covered:

| Condition class | Valid operators |
|---|---|
| `HostGroupCondition` | EQUALS, NOT_EQUALS |
| `HostCondition` | EQUALS, NOT_EQUALS |
| `TriggerCondition` | EQUALS, NOT_EQUALS |
| `EventNameCondition` | CONTAINS, NOT_CONTAINS |
| `SeverityCondition` | EQUALS, NOT_EQUALS, GREATER_OR_EQUAL, LESS_OR_EQUAL |
| `TriggerValueCondition` | EQUALS |
| `TimePeriodCondition` | IN, NOT_IN |
| `HostIPCondition` | EQUALS, NOT_EQUALS |
| `DiscoveredServiceTypeCondition` | EQUALS, NOT_EQUALS |
| `DiscoveredServicePortCondition` | EQUALS, NOT_EQUALS |
| `DiscoveryStatusCondition` | EQUALS |
| `UptimeCondition` | GREATER_OR_EQUAL, LESS_OR_EQUAL |
| `ReceivedValueCondition` | EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS, GREATER_OR_EQUAL, LESS_OR_EQUAL |
| `HostTemplateCondition` | EQUALS, NOT_EQUALS |
| `SuppressedCondition` | YES, NO |
| `DiscoveryRuleCondition` | EQUALS, NOT_EQUALS |
| `DiscoveryCheckCondition` | EQUALS, NOT_EQUALS |
| `ProxyCondition` | EQUALS, NOT_EQUALS |
| `DiscoveryObjectCondition` | EQUALS |
| `HostNameCondition` | CONTAINS, NOT_CONTAINS, MATCHES, NOT_MATCHES |
| `EventTypeCondition` | EQUALS |
| `HostMetadataCondition` | CONTAINS, NOT_CONTAINS, MATCHES, NOT_MATCHES |
| `TagCondition` | EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS |
| `TagValueCondition` | EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS |
| `ServiceCondition` | EQUALS, NOT_EQUALS |
| `ServiceNameCondition` | EQUALS, NOT_EQUALS |

### ConditionList

Use `ConditionList` when Zabbix should handle grouping according to `evaltype`:

```python
from zbxtemplar.decree.action_conditions import ConditionList, EvalType
from zbxtemplar.decree.action_conditions import HostGroupCondition, SeverityCondition

conditions = ConditionList(EvalType.AND_OR)
conditions.add(HostGroupCondition("Production"))
conditions.add(HostGroupCondition("Staging"))
conditions.add(SeverityCondition("HIGH"))
```

### Expression Trees With Auto-Formula

Use `&`, `|`, and `~` for formula-style logic. zbxtemplar automatically assigns formula labels, generates the formula string, and handles parenthesization:

```python
prod = HostGroupCondition("Production")
stage = HostGroupCondition("Staging")
high = SeverityCondition("HIGH")
suppressed = SuppressedCondition()

expr = (prod | stage) & high & ~suppressed
```

This generates:

```json
{
    "evaltype": 3,
    "formula": "(A or B) and C and not D",
    "conditions": [
        {"conditiontype": 0, "operator": 0, "value": "Production", "formulaid": "A"},
        {"conditiontype": 0, "operator": 0, "value": "Staging", "formulaid": "B"},
        {"conditiontype": 4, "operator": 5, "value": "HIGH", "formulaid": "C"},
        {"conditiontype": 16, "operator": 11, "formulaid": "D"}
    ]
}
```

No manual label assignment. No manual formula string. Correct precedence.

`ConditionExpr.__bool__()` raises a `TypeError`, which means Python `and` and `or` are rejected on purpose with a clear error message. Use `&`, `|`, and `~` instead.

---

## Trigger Actions

`TriggerAction` has three typed operation containers:

```
TriggerAction
├── operations             (TriggerOperations)         — with escalation steps
├── recovery_operations    (TriggerAckOperations)      — no escalation steps
└── update_operations      (TriggerAckOperations)      — no escalation steps
```

You cannot set escalation steps on a recovery operation — it is structurally impossible.

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

`AutoregistrationAction` has a single operation container with host-management methods:

```
AutoregistrationAction
└── operations    (AutoregistrationOperations)
    ├── send_message()
    ├── add_host()
    ├── add_to_group()
    ├── link_template()
    ├── enable_host() / disable_host()
    └── set_inventory_mode()
```

You cannot call `add_host()` on a `TriggerAction`. Wrong combinations are structurally impossible.

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

---

## Context Validation

When actions reference templates, groups, or other generated objects, use `--context` to validate those references at generation time — before any YAML is produced, before any API call happens:

```python
class MyDecree(DecreeModule):
    def compose(self):

        prod_group = self.context.get_host_group("Production")
        web_template = self.context.get_template("Web Server Template")

        action = self.add_trigger_action("Notify production incidents")
        action.set_conditions(
            HostGroupCondition(prod_group) & HostTemplateCondition(web_template)
        )
```

`self.context.get_host_group("Prodction")` raises `ValueError: Host group 'Prodction' not found in context` during `zbxtemplar decree.py -o decree.yml --context templates.yml`. Not during `zbxtemplar-exec apply` against production.

This creates a two-stage safety net:

| Stage | What happens | Catches |
|-------|-------------|---------|
| **Generation time** | Context validates referenced names exist | Typos, missing references |
| **Apply time** | Executor resolves names to Zabbix IDs | Objects that exist in config but not yet in Zabbix |

The cheapest failures happen first.

---

## Trigger Expressions

`Item.expr()` generates correct Zabbix trigger expression paths from the item's owning entity:

```python
item.add_trigger("CPU High", fn="last", op=">", threshold=90, priority=TriggerPriority.HIGH)
# generates: last(/Template Name/item.key)>90

# Or compose manually for multi-item expressions:
full_expr = f"{cpu_item.expr('avg', '5m')}>{threshold}"
template.add_trigger("CPU Average High", full_expr, TriggerPriority.WARNING)
```

The `/{host}/{key}` path is generated automatically — no manual string construction needed.

---

## Name Resolution at Apply Time

Decree YAML uses names, not IDs. The executor resolves them to live Zabbix IDs at runtime:

- Action condition values: host group, host, trigger, template names to IDs
- Operation targets: user group, user, media type names to IDs

This keeps decree YAML readable and reviewable while still working against any Zabbix instance.

---

## Current Coverage

Implemented today:

- Trigger actions: send-message operations (main, recovery, update)
- Autoregistration actions: send-message, add-host, add-to-group, link-template, enable/disable-host, set-inventory-mode

Not yet implemented as first-class types:

- Discovery actions
- Internal actions
- Remote command operations
- Trigger host-management operations

## Practical Advice

- Start with send-message operations — they are the most complete path today.
- Use `--context` when your action references templates, groups, or other generated objects.
- Keep decree action definitions readable; name-based references are a feature.
