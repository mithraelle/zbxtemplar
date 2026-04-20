# Templates & Hosts

`self.*` calls below are `TemplarModule` methods called from inside `compose()`.

## Imports

```python
from zbxtemplar.modules import TemplarModule
from zbxtemplar.zabbix.Template import TemplateGroup, ValueMap, ValueMapType
from zbxtemplar.zabbix.Host import HostGroup, AgentInterface
from zbxtemplar.zabbix import MacroType
```

## Groups

`TemplateGroup` and `HostGroup` are created automatically if missing when the executor imports
the YAML. All Zabbix-native objects (groups, templates, hosts, items, triggers, graphs,
dashboards, value maps) follow the same rule: `createMissing: true, updateExisting: true`.

```python
tg = TemplateGroup("My Templates")
hg = HostGroup("My Hosts")
```

## Template

```python
template = self.add_template("My Template", groups=[tg])
template.add_tag("Service", "monitoring")  # value is optional, defaults to ""
```

Raises `ValueError` on duplicate name within the module.

### Macros

```python
m = template.add_macro("MY_MACRO", "value", "description")
m = template.add_macro("MY_SECRET", "s3cr3t", "desc", MacroType.SECRET_TEXT)
# MacroType: TEXT (default), SECRET_TEXT (alias: SECRET), VAULT
# Name is stored without braces; {$MY_MACRO} and MY_MACRO are equivalent

val = template.get_macro("MY_MACRO")   # searches: own → linked templates → module level
val.value                              # the macro value as string
```

### Value maps

```python
vm = ValueMap("Status Map")
vm.add_mapping("1", "UP", ValueMapType.EQUAL)
vm.add_mapping("0", "DOWN", ValueMapType.EQUAL)
# ValueMapType: EQUAL, GREATER_OR_EQUAL, LESS_OR_EQUAL, IN_RANGE, REGEXP, DEFAULT
template.add_value_map(vm)
```

### Value maps

Same API as templates — `host.add_value_map(vm)` works identically.

### Linked templates

```python
template.add_template(other_template)
```

## Host

```python
host = self.add_host("my-host", groups=[hg])
host.add_tag("env", "prod")               # value is optional, defaults to ""
host.add_template(template)
```

Raises `ValueError` on duplicate name within the module.

### Interfaces

```python
iface = AgentInterface(ip="192.168.1.10", port="10050")  # defaults: 127.0.0.1:10050
host.add_interface(iface)   # first added becomes the default interface
```

### Macros on hosts

Same API as templates. `get_macro()` searches own → linked templates → module level.

```python
m = host.add_macro("MY_HOST_MACRO", "value", "desc")
host.get_macro("MY_HOST_MACRO").value
```