# Getting Started

## Installation

Install the generator:

```bash
pip install .
```

Install the executor as well:

```bash
pip install '.[executor]'
```

`zbxtemplar` requires Python 3.11 or newer.

## First Monitoring Module

Create a Python file with a `TemplarModule` subclass:

```python
from zbxtemplar.modules import TemplarModule
from zbxtemplar.zabbix import Item, TriggerPriority
from zbxtemplar.zabbix.Template import TemplateGroup
from zbxtemplar.zabbix.Host import HostGroup, AgentInterface


class MyModule(TemplarModule):
    def compose(self, alert_threshold: int = 90):

        template = self.add_template(
            name="My Service",
            groups=[TemplateGroup("Custom Templates")],
        )
        template.add_macro("THRESHOLD", alert_threshold, "Alert threshold")

        item = Item("CPU Usage", "system.cpu.util", template.name)
        item.add_trigger(
            "High CPU",
            "last",
            ">",
            template.get_macro("THRESHOLD"),
            priority=TriggerPriority.HIGH,
        )
        template.add_item(item)

        host = self.add_host("My Server", groups=[HostGroup("Linux Servers")])
        host.add_template(template)
        host.add_interface(AgentInterface(ip="192.168.1.10"))
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

Use `DecreeModule` when you need users, groups, or actions:

```python
from zbxtemplar.modules import DecreeModule
from zbxtemplar.decree import Token, UserMedia
from zbxtemplar.decree import GuiAccess, Permission, Severity
from zbxtemplar.decree import MediaType, UserRole


class MyDecree(DecreeModule):
    def compose(self, alert_email: str = "alerts@example.com"):

        group = self.add_user_group("Operations", gui_access=GuiAccess.INTERNAL)
        group.add_host_group("Linux Servers", Permission.READ)

        user = self.add_user("zbx-ops", role=UserRole.ADMIN)
        user.add_group(group)

        email = UserMedia(MediaType.EMAIL, alert_email)
        email.set_severity([Severity.HIGH, Severity.DISASTER])
        user.add_media(email)

        user.set_token(
            Token(
                name="zbx-ops-api",
                store_at=".secrets/zbx-ops-api.token",
                expires_at=Token.NEVER,
            )
        )
```

Generate decree YAML:

```bash
zbxtemplar decree_module.py -o decree.yml --context templates.yml
```

`--context` lets a module reference known objects from YAML context files. Those files can come from previously generated artifacts or from existing exported configuration.

Token provisioning uses a nested `token` object under the user. At minimum it needs a token name, an expiration for create-time provisioning, and an output sink `store_at` (which can be a file path or `STDOUT`).

## Apply The Output

For Zabbix-native YAML:

```bash
zbxtemplar-exec apply templates.yml --url https://zabbix.example.com --token "$ZABBIX_TOKEN"
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
- Read [Generator Guide](./generator.md) for CLI and module-loading details.
- Read [Executor Guide](./executor.md) before applying to a live instance.
