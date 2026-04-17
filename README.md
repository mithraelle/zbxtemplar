# zbxtemplar

A Pythonic framework for programmatic Zabbix configuration generation — Monitoring as Code.

Define templates, hosts, user groups, users, and actions as Python code. Generate Zabbix-native YAML (importable via UI or API) and decree YAML (applied by the executor). The goal is to cover the essential Zabbix configuration primitives — not every possible option. If you need a field that isn't exposed, raw dicts and string expressions give you an escape hatch.

Aimed at teams that want:

- monitoring configuration in git, reviewable in PRs
- readable, programmable definitions instead of large generated exports
- a lightweight way to manage users, permissions, and alert-routing state
- confidence that deploying monitoring configuration cannot accidentally leak credentials, partially apply state, or silently ignore misconfiguration
- a structured, sequenced run trace that records every file loaded, every entity created or updated with its live ID, and every secret write — without ever logging a secret value

## Why

Zabbix is powerful, but its configuration is not pleasant to version, review, or evolve in code. Terraform and Ansible can manage Zabbix — they bring ceremony and templating complexity that often outweigh the problem. Monitoring is combinatorial: an application across a dozen regions, each with a set of queues, each queue needing several items, a dashboard per region, an overview graph. Hundreds of objects, nearly identical but each distinct. In HCL or Jinja, the template becomes harder to read than the output. In `zbxtemplar`, it is a loop and a set of parameters — plain Python any developer on the team can read.

The Zabbix UI handles one-off setup fine. The trouble starts when you need the same action across dev, staging, and prod. When someone edits an alert filter and nobody notices until production goes silent. When "for each team, create a scoped alert" means N manual repetitions with N chances to get it wrong. That does not scale — which forces you into code.

Once you are there, secrets need handling. `${ENV_VAR}` placeholders keep credentials out of git; a missing variable is a hard abort, not an empty string applied to a live instance. Zabbix `secret` and `vault` macro types are first-class. Host encryption (PSK, TLS certificates) and token provisioning — things that are clunky or impossible to automate from the web interface — are managed declaratively with the same strict contract ([`doc/security.md`](./doc/security.md)).

Actions are where the Zabbix API gets awkward and error-prone: numeric codes for everything, manual formula labels, invalid operator-condition combinations accepted without complaint. `zbxtemplar` replaces that with typed Python — `HostGroupCondition("Production") & SeverityCondition("HIGH")`. Names, not IDs. Wrong operator on the wrong condition type? Type error at write time, not a silent misfire during an incident ([`doc/actions.md`](./doc/actions.md)).

Macros follow a layered resolution chain: entity macros → linked template macros → module-level macros → context macros. Module-level macros (`self.add_macro(...)` inside `__init__`) act as the global tier — shared across every template and host in the module and exported as `set_macro` YAML for the executor to apply.

On top of all this, `Context` validates references at generation time — against previously generated or exported YAML. Additionally, the executor applies **fail-fast typo checking** to your `decree` YAML configurations. A typo in a host group name, a missing template, or even misspelling a configuration key (like `expire_at` instead of `expires_at`) halts execution *before* any mutating API calls are made. Deterministic UUIDs prevent import duplicates. Mistakes break against your code, not against production ([`doc/generator.md`](./doc/generator.md)).

## What It Does

`zbxtemplar` has three main pieces:

- `TemplarModule` generates Zabbix-native YAML for templates and hosts
- `DecreeModule` generates decree YAML for users, user groups, and actions
- `zbxtemplar-exec` applies generated artifacts to a live Zabbix instance

The split is intentional:

- monitoring objects fit well into Zabbix's native import/export model
- user management and action state often need API-driven apply logic
- both outputs stay reviewable as plain YAML artifacts

## Quick Example

```python
from zbxtemplar.modules import TemplarModule
from zbxtemplar.zabbix import Item, TriggerPriority
from zbxtemplar.zabbix.Template import TemplateGroup
from zbxtemplar.zabbix.Host import HostGroup, AgentInterface


class MyModule(TemplarModule):
    def __init__(self, alert_threshold: int = 90):
        super().__init__()

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

Apply it:

```bash
zbxtemplar-exec apply monitoring.yml \
  --url https://zabbix.example.com \
  --token "$ZABBIX_TOKEN"
```

## Installation

Install the generator:

```bash
pip install .
```

Install the executor as well:

```bash
pip install '.[executor]'
```

Python 3.11+ is required.

## Typical Workflow

1. Write a Python module using `TemplarModule` or `DecreeModule`.
2. Generate YAML with `zbxtemplar`.
3. Review the generated artifacts in git.
4. Validate against a test Zabbix instance.
5. Apply to production with `zbxtemplar-exec` when ready.

This project assumes a test-environment-first workflow rather than a separate dry-run engine.

## Documentation

The [`examples/`](./examples/) directory contains complete working modules (`make_template.py`, `make_decree.py`), the sample YAML artifacts they generate, and a reference scroll (`sample_scroll.yml`).

The structured docs live in [`doc/`](./doc/README.md):

- [`doc/getting-started.md`](./doc/getting-started.md) for the first end-to-end workflow
- [`doc/architecture.md`](./doc/architecture.md) for the mental model
- [`doc/generator.md`](./doc/generator.md) for CLI and module-loading behavior
- [`doc/executor.md`](./doc/executor.md) for apply/decree/scroll usage
- [`doc/actions.md`](./doc/actions.md) for action conditions and operations
- [`doc/security.md`](./doc/security.md) for the operational safety model
- [`doc/decree_reference.md`](./doc/decree_reference.md) for the generated YAML schema reference

## Current Scope

`zbxtemplar` is already useful, but it is still a working tool rather than a polished platform.

Good fit:

- teams that want reviewable monitoring definitions in Python
- repositories where monitoring config should live close to service code
- environments where users, permissions, and alert-routing changes need to be scripted cleanly

Things to know:

- the docs in `doc/` are the public technical reference
- the project is intentionally opinionated about the main workflow
- the executor is practical, but not presented as a fully hardened unattended deployment system

## License

MIT
