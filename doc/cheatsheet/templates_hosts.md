# Templates & Hosts

`self.*` calls below are `TemplarModule` methods called from inside `compose()`.

## Imports

```python
from zbxtemplar.modules import TemplarModule
from zbxtemplar.zabbix.Template import TemplateGroup, ValueMapType
from zbxtemplar.zabbix.Host import HostGroup, AgentInterface
from zbxtemplar.zabbix import MacroType, InventoryMode
from zbxtemplar.catalog.zabbix_7_4 import InventoryField
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
vm = template.add_value_map("Status Map")
vm.add_mapping("1", "UP", ValueMapType.EQUAL)
vm.add_mapping("0", "DOWN", ValueMapType.EQUAL)
# ValueMapType: EQUAL, GREATER_OR_EQUAL, LESS_OR_EQUAL, IN_RANGE, REGEXP, DEFAULT
```

### Value maps

Same API as templates — `host.add_value_map(vm)` works identically.

### Linked templates

```python
template.link_template(other_template)
```

## Host

```python
host = self.add_host("my-host", groups=[hg])
host.add_tag("env", "prod")               # value is optional, defaults to ""
host.link_template(template)
```

Raises `ValueError` on duplicate name within the module.

### Interfaces

```python
iface = AgentInterface(ip="192.168.1.10", port="10050")  # defaults: 127.0.0.1:10050
host.link_interface(iface)   # first added becomes the default interface
```

### Macros on hosts

Same API as templates. `get_macro()` searches own → linked templates → module level.

```python
m = host.add_macro("MY_HOST_MACRO", "value", "desc")
host.get_macro("MY_HOST_MACRO").value
```

### Inventory

Zabbix host inventory is a fixed set of ~70 asset-tracking fields (os, hardware, contact,
location, ...). Fields are populated manually via the host config, or automatically from
item values in `AUTOMATIC` mode (see `Item.set_inventory_link()` in
[`items_triggers.md`](items_triggers.md)).

```python
host.set_inventory_mode(InventoryMode.MANUAL)
host.set_inventory(InventoryField.OS, "Linux")
host.set_inventory(InventoryField.LOCATION, "DC1 Rack 12")
host.set_inventory(InventoryField.CONTACT, "ops@example.com")
```

**InventoryMode:** DISABLED, MANUAL, AUTOMATIC

**InventoryField** (from `zbxtemplar.catalog.zabbix_7_4`) covers the full Zabbix 7.4 field list: ALIAS, OS, OS_FULL, OS_SHORT,
HARDWARE, HARDWARE_FULL, SOFTWARE, SOFTWARE_FULL, SERIALNO_A, SERIALNO_B, TAG, ASSET_TAG,
MACADDRESS_A, MACADDRESS_B, CHASSIS, MODEL, VENDOR, HW_ARCH, CONTACT, LOCATION,
LOCATION_LAT, LOCATION_LON, NOTES, CONTRACT_NUMBER, INSTALLER_NAME, DEPLOYMENT_STATUS,
URL_A/B/C, HOST_NETWORKS, HOST_NETMASK, HOST_ROUTER, OOB_IP, OOB_NETMASK, OOB_ROUTER,
DATE_HW_PURCHASE / _INSTALL / _EXPIRY / _DECOMM, SITE_ADDRESS_A/B/C, SITE_CITY, SITE_STATE,
SITE_COUNTRY, SITE_ZIP, SITE_RACK, SITE_NOTES, POC_1_* and POC_2_* (NAME, EMAIL, PHONE_A/B,
CELL, SCREEN, NOTES), plus TYPE, TYPE_FULL, NAME, SOFTWARE_APP_A..E.

`Host.to_dict()` raises `ValueError` on two incoherent combinations that Zabbix would
silently drop on import:

- `inventory` fields set but `inventory_mode` left unset
- `inventory` fields set together with `InventoryMode.DISABLED`

An `inventory_link` set on a template/host item is **not** inspected: Zabbix harmlessly
ignores it when the host is in `MANUAL` or `DISABLED` mode, and the same template may be
reused across hosts of varying modes.