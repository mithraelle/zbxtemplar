# Getting Started

## Installation

```bash
pip install .
```

`zbxtemplar` requires Python 3.11 or newer. The install provides both the generator (`zbxtemplar`) and the executor (`zbxtemplar-exec`).

## First Monitoring Module

Create a Python file with a `TemplarModule` subclass:

```python
from zbxtemplar.modules import TemplarModule
from zbxtemplar.zabbix import TriggerPriority, InventoryMode, TemplateGroup, HostGroup, AgentInterface
from zbxtemplar.catalog.zabbix_7_4 import functions, InventoryField


class MyModule(TemplarModule):
    def compose(self, alert_threshold: int = 90):

        template = self.add_template(
            name="My Service",
            groups=[TemplateGroup("Custom Templates")],
        )
        threshold_macro = template.add_macro("THRESHOLD", alert_threshold, "Alert threshold")

        item = template.add_item("CPU Usage", "system.cpu.util")
        template.add_trigger(
            name="High CPU",
            expression=functions.history.Last(item) > threshold_macro,
            priority=TriggerPriority.HIGH,
        )

        os_item = template.add_item("OS version", "system.sw.os")
        os_item.set_inventory_link(InventoryField.OS)

        host = self.add_host("My Server", groups=[HostGroup("Linux Servers")])
        host.link_template(template)
        host.link_interface(AgentInterface(ip="192.168.1.10"))
        host.set_inventory_mode(InventoryMode.AUTOMATIC)
        host.set_inventory(InventoryField.LOCATION, "DC1 Rack 12")
```


Generate YAML:

```bash
zbxtemplar my_module.py -o monitoring.yml
```

Or split templates and hosts:

```bash
zbxtemplar my_module.py \
  --templates-output templates.yml \
  --hosts-output hosts.yml
```

## First Decree Module

Use `DecreeModule` when you need users, groups, SAML, host encryption, global macros, or actions:

```python
from zbxtemplar.modules import DecreeModule
from zbxtemplar.decree import Token
from zbxtemplar.decree import GuiAccess, Permission, Severity
from zbxtemplar.catalog.zabbix_7_4 import MediaType, UserRole


class MyDecree(DecreeModule):
    def compose(self, alert_email: str = "alerts@example.com"):

        group = self.add_user_group("Operations", gui_access=GuiAccess.INTERNAL)
        group.link_host_group("Linux Servers", Permission.READ)

        user = self.add_user("zbx-ops", role=UserRole.ADMIN)
        user.link_group(group)

        user.add_media(MediaType.EMAIL, alert_email).set_severity(
            [Severity.HIGH, Severity.DISASTER]
        )

        user.set_token(
            "zbx-ops-api",
            store_at=".secrets/zbx-ops-api.token",
            expires_at=Token.EXPIRES_NEVER,
        )
```

Generate decree YAML:

```bash
zbxtemplar decree_module.py -o decree.yml --context monitoring.yml
```

`--context` lets a module reference known objects from YAML context files. Those files can come from previously generated artifacts or from existing exported configuration.

Token provisioning uses a nested `token` object under the user. At minimum it needs a token name, an expiration for create-time provisioning, and an output sink `store_at` (which can be a file path or `STDOUT`).

SAML and host encryption use the same decree output. The module helpers are `set_saml(...)`, `set_encryption_defaults(...)`, and `add_host_encryption(...)`; see the Executor Guide and Decree Reference for the fields applied to Zabbix.

## Apply The Output

For Zabbix-native YAML:

```bash
zbxtemplar-exec apply monitoring.yml --url https://zabbix.example.com --token "$ZABBIX_TOKEN"
```

For decree YAML:

```bash
zbxtemplar-exec apply decree.yml --url https://zabbix.example.com --token "$ZABBIX_TOKEN"
```

## Expected Workflow

The intended operating model is:

1. Generate artifacts from Python.
2. Review those artifacts.
3. Validate on a test Zabbix instance.
4. Apply to production once the result looks right.

This project assumes "test environment first" rather than a separate dry-run simulator.

One important implementation detail: `--context` is loaded once for the module run and exposed as `self.context` inside both `TemplarModule` and `DecreeModule`.

## Where To Go Next

- Browse [`examples/`](../examples/) for complete working modules, sample YAML artifacts, and a reference scroll.
- Read [Architecture](./architecture.md) for the overall design.
- Read [Authoring Monitoring](./authoring-monitoring.md), [Authoring Decree](./authoring-decree.md), or [Authoring Actions](./authoring-actions.md) for the authoring surface you need.
- Read [CLI Reference](./cli-reference.md) for flags, `--param`, `--context`, and module-loading details.
- Read [Executor Guide](./executor.md) before applying to a live instance.
