# Items & Triggers

Items and triggers are built inside `compose()` and added to a `Template` or `Host` object.

## Imports

```python
from zbxtemplar.zabbix.Item import ItemType, ValueType
from zbxtemplar.zabbix.Trigger import TriggerPriority
from zbxtemplar.catalog.zabbix_7_4 import functions, InventoryField
```

## Item

```python
item = template.add_item(
    name="CPU load",
    key="system.cpu.load[,avg1]",
    type=ItemType.ZABBIX_PASSIVE,  # default
    value_type=ValueType.FLOAT,
    history="90d",
    trends="365d",
)
# also: host.add_item(...)
item.add_tag("Service", "monitoring")   # value optional, defaults to ""
```

**ItemType:** ZABBIX_PASSIVE, ZABBIX_ACTIVE, TRAP, SIMPLE, INTERNAL, EXTERNAL, ODBC, IPMI,
SSH, TELNET, CALCULATED, JMX, SNMP_TRAP, SNMP_AGENT, DEPENDENT, HTTP_AGENT,
ITEM_TYPE_SCRIPT, ITEM_TYPE_BROWSER

**ValueType:** UNSIGNED (default), FLOAT, CHAR, LOG, TEXT, BINARY

### Common settings

```python
item.set_delay("30s")              # update interval; Zabbix default is 1m; macros allowed
item.set_units("%")
item.set_description("Load average over 1 minute")
item.set_state(enabled=False)      # disable the item
```

All setters return the item, so they chain.

### Other item fields

Fields without a setter can be set as plain attributes, using their Zabbix export names; they
are written to the YAML unchanged:

```python
snmp = template.add_item("Load", "snmp.load", type=ItemType.SNMP_AGENT)
snmp.snmp_oid = "1.3.6.1.4.1.2021.10.1.3.1"
snmp.preprocessing = [{"type": "MULTIPLIER", "parameters": ["100"]}]
```

A misspelled field name is rejected by Zabbix on import.

### Value map

```python
item.link_value_map(value_map)   # ValueMap object defined on the same template
```

### Interface (hosts only)

```python
item.link_interface(iface)   # AgentInterface assigned to the host
```

### Inventory link

Populate a host inventory field automatically from this item's collected value. Only
takes effect when the owning host is in `InventoryMode.AUTOMATIC`; Zabbix ignores the
link in `MANUAL` or `DISABLED` mode.

```python
item.set_inventory_link(InventoryField.OS)
```

See [`templates_hosts.md`](templates_hosts.md#inventory) for the full field list and the
host-side `set_inventory_mode()` / `set_inventory()` API.

## Trigger expression builder

Trigger expressions are Python expression trees. Wrap items with trigger function
classes from `zbxtemplar.catalog.zabbix_7_4.functions`, then combine them with Python
operators.

```python
functions.history.Last(item)             # last(/Template/key)
functions.aggregate.Min(item, "5m")      # min(/Template/key,5m)
functions.aggregate.Avg(item, "10m")     # avg(/Template/key,10m)
```

Use normal comparison and arithmetic operators. Use `&`, `|`, and `~` for
Zabbix `and`, `or`, and `not`.

```python
expr = functions.aggregate.Avg(item1, "5m") > 90
expr = functions.history.Last(item1) > macro   # macro renders as {$MY_MACRO}
expr = ((functions.history.Last(item1) > macro)
        & (functions.history.Last(item2) < 10))
expr = ~(functions.history.Last(item1) == 0)    # renders as not (last(...) = 0)
expr = functions.history.Last(item1) != 0       # renders as last(...) <> 0
```

See [trigger_functions_glossary.md](trigger_functions_glossary.md) for the
available trigger function wrappers.

## Single-item trigger

Pass an expression tree to `add_trigger()`. Expressions referencing one item are
emitted under that item in the Zabbix export.

```python
template.add_trigger(
    name="High CPU",
    expression=functions.aggregate.Avg(item, "5m") > 90,
    priority=TriggerPriority.HIGH,
    description="optional description",
)
```

**TriggerPriority:** NOT_CLASSIFIED, INFO, WARNING, AVERAGE, HIGH, DISASTER

`add_trigger()` returns the `Trigger` regardless of where it is emitted — capture it to
add tags.

## Multi-item trigger

Expressions referencing multiple items stay on the owning template or host.

```python
expr = ((functions.history.Last(item1) > 100)
        & (functions.history.Last(item2) < 0))
trigger = template.add_trigger(
    name="Complex condition",
    expression=expr,
    priority=TriggerPriority.WARNING,
    description="optional",
)
trigger.add_tag("scope", "availability")   # Trigger also supports add_tag()
# also: host.add_trigger(...)
```

## Trigger lookup

`get_trigger(name)` returns a trigger by name from a template or host, wherever it is
emitted (under an item or on the owner). Raises `KeyError` if not found.

```python
trigger = template.get_trigger("High CPU")
# also: host.get_trigger(...)
```

Use it in a decree module to reference a trigger from a `--context` host in a trigger
condition:

```python
host = self.context.get_host("Templar Host")
action.set_conditions(TriggerCondition(host.get_trigger("Host Simple trigger")))
```
