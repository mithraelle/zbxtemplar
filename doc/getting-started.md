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

`zbxtemplar` requires Python 3.9 or newer.

## First Monitoring Module

Create a Python file with a `TemplarModule` subclass:

```python
from zbxtemplar.core import TemplarModule
from zbxtemplar.zabbix import Template, Item, Host, TriggerPriority
from zbxtemplar.zabbix.Template import TemplateGroup
from zbxtemplar.zabbix.Host import HostGroup, AgentInterface


class MyModule(TemplarModule):
    def __init__(self, alert_threshold: int = 90, context=None):
        super().__init__(context=context)

        template = Template(
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

        host = Host("My Server", groups=[HostGroup("Linux Servers")])
        host.add_template(template)
        host.add_interface(AgentInterface(ip="192.168.1.10"))

        self.add_template(template)
        self.add_host(host)
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
from zbxtemplar.core import DecreeModule
from zbxtemplar.decree import UserGroup, User, UserMedia
from zbxtemplar.decree import GuiAccess, Permission, Severity
from zbxtemplar.decree import MediaType, UserRole


class MyDecree(DecreeModule):
    def __init__(self, alert_email: str = "alerts@example.com", context=None):
        super().__init__(context=context)

        group = UserGroup("Operations", gui_access=GuiAccess.INTERNAL)
        group.add_host_group("Linux Servers", Permission.READ)
        self.add_user_group(group)

        user = User("zbx-ops", role=UserRole.ADMIN)
        user.add_group(group)

        email = UserMedia(MediaType.EMAIL, alert_email)
        email.set_severity([Severity.HIGH, Severity.DISASTER])
        user.add_media(email)

        self.add_user(user)
```

Generate decree YAML:

```bash
zbxtemplar decree_module.py -o decree.yml --context templates.yml
```

`--context` lets a module reference known objects from YAML context files. Those files can come from previously generated artifacts or from existing exported configuration.

## Apply The Output

For Zabbix-native YAML:

```bash
zbxtemplar-exec apply templates.yml --url https://zabbix.example.com --token "$ZABBIX_TOKEN"
```

For decree YAML:

```bash
zbxtemplar-exec decree decree.yml --url https://zabbix.example.com --token "$ZABBIX_TOKEN"
```

## Expected Workflow

The intended operating model is:

1. Generate artifacts from Python.
2. Review those artifacts.
3. Validate on a test Zabbix instance.
4. Apply to production once the result looks right.

This project assumes "test environment first" rather than a separate dry-run simulator.

One important implementation detail: `--context` is forwarded into module constructors when their `__init__` includes a `context` parameter. This applies to both `TemplarModule` and `DecreeModule`. If you override `__init__`, include `context=None` and pass it to `super().__init__(context=context)` to consume it in the module.

## Where To Go Next

- Read [Architecture](./architecture.md) for the overall design.
- Read [Generator Guide](./generator.md) for CLI and module-loading details.
- Read [Executor Guide](./executor.md) before applying to a live instance.
