# Items & Triggers

Items and triggers are built inside `compose()` and added to a `Template` or `Host` object.

## Imports

```python
from zbxtemplar.zabbix.Item import ItemType, ValueType
from zbxtemplar.zabbix.Trigger import TriggerPriority
from zbxtemplar.zabbix import functions, InventoryField
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
classes from `zbxtemplar.zabbix.functions`, then combine them with Python
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
