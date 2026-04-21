# Items & Triggers

Items and triggers are built inside `compose()` and added to a `Template` or `Host` object.

## Imports

```python
from zbxtemplar.zabbix.Item import ItemType, ValueType
from zbxtemplar.zabbix.Trigger import TriggerPriority
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

## Trigger expression helper

`item.expr(fn, *args)` returns a string fragment for building expressions manually.

```python
item.expr("last")          # →  "last(/Template/key)"
item.expr("min", 5)        # →  "min(/Template/key,5)"
item.expr("avg", "5m")     # →  "avg(/Template/key,5m)"
```

Concatenate with strings to build full expressions:

```python
expr = item1.expr("avg", "5m") + ">" + "90"
expr = item1.expr("last") + ">" + str(macro)   # str(macro) → "{$MY_MACRO}"
expr = (item1.expr("last") + ">" + str(macro)
        + " and " + item2.expr("last") + "<" + "10")
```

## Single-item trigger (shortcut)

Builds the expression automatically from the item.

```python
item.add_trigger(
    name="High CPU",
    fn="avg",              # Zabbix function name
    op=">",                # operator string: >, <, >=, <=, =, <>
    threshold=90,          # int, float, str, or Macro object (renders as {$NAME} automatically)
    fn_args=("5m",),       # additional args passed to fn: avg(/key,5m)
    priority=TriggerPriority.HIGH,
    description="optional description",
)
```

**TriggerPriority:** NOT_CLASSIFIED, INFO, WARNING, AVERAGE, HIGH, DISASTER

## Multi-item trigger

Pass a pre-built expression string to `add_trigger()` on the template or host.

```python
expr = item1.expr("last") + ">" + "100 and " + item2.expr("last") + "<" + "0"
trigger = template.add_trigger(
    name="Complex condition",
    expression=expr,
    priority=TriggerPriority.WARNING,
    description="optional",
)
trigger.add_tag("scope", "availability")   # Trigger also supports add_tag()
# also: host.add_trigger(...)
```