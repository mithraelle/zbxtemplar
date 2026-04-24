# zbxtemplar

A Pythonic framework for programmatic Zabbix configuration generation — Monitoring as Code.

Define templates, hosts, user groups, users, SAML directories, actions, and host encryption as Python code. `TemplarModule` emits Zabbix-native YAML (importable via UI or API); `DecreeModule` emits decree YAML (applied by `zbxtemplar-exec`). The goal is to cover the essential Zabbix configuration primitives — not every possible option. If you need a field that isn't exposed, raw dicts provide an escape hatch.

Aimed at teams that want:

- monitoring configuration in git, reviewable in PRs
- readable, programmable definitions instead of large generated exports
- a lightweight way to manage users, permissions, SAML JIT provisioning, and alert-routing state
- confidence that deploying monitoring configuration cannot accidentally leak credentials, partially apply state, or silently ignore misconfiguration
- a structured, sequenced run trace that records every file loaded, every entity created or updated with its live ID, and every secret write — without ever logging a secret value

## Why

Zabbix is powerful, but its configuration is not pleasant to version, review, or evolve in code. Terraform and Ansible can manage Zabbix — they bring ceremony and templating complexity that often outweigh the problem. Monitoring is combinatorial: an application across a dozen regions, each with a set of queues, each queue needing several items, a dashboard per region, an overview graph. Hundreds of objects, nearly identical but each distinct. In HCL or Jinja, the template becomes harder to read than the output. In `zbxtemplar`, it is a loop and a set of parameters — plain Python any developer on the team can read.

The Zabbix UI handles one-off setup fine. The trouble starts when you need the same action across dev, staging, and prod. When someone edits an alert filter and nobody notices until production goes silent. When "for each team, create a scoped alert" means N manual repetitions with N chances to get it wrong. That does not scale — which forces you into code.

Once you are there, secrets need handling. `${ENV_VAR}` placeholders keep credentials out of git; a missing variable is a hard abort, not an empty string applied to a live instance. Zabbix `secret` and `vault` macro types are first-class. Host encryption (PSK, TLS certificates), API token provisioning, and **SAML Single Sign-On (SSO) with JIT user provisioning** — things that are clunky or impossible to automate from the web interface — are managed declaratively with the same strict contract (see [Security & Safety](./doc/security.md)).

Actions are where the Zabbix API gets awkward and error-prone: numeric codes for everything, manual formula labels, invalid operator-condition combinations accepted without complaint. `zbxtemplar` replaces that with typed Python — `HostGroupCondition("Production") & SeverityCondition("HIGH")`. Names, not IDs. Wrong operator on the wrong condition type? Type error at write time, not a silent misfire during an incident (see [Authoring Actions](./doc/authoring-actions.md)).

Trigger expressions are equally frustrating to write by hand: string concatenation, escaping issues, and manual resolution of item paths. `zbxtemplar` provides a **Trigger Expression Builder** using native Python syntax. You wrap items in typed function wrappers (e.g., `functions.history.Last(item)`) and combine them with normal arithmetic and bitwise operators (`>`, `&`, `~`). The builder handles rendering the complex Zabbix expression string format for you, with type-hinted support for all Zabbix 7.4 trigger functions (see [Authoring Monitoring](./doc/authoring-monitoring.md)).

Zabbix itself does not hold still between releases — new trigger functions, added inventory fields, renamed media types. A framework that bakes that moving vocabulary into its core ages badly against a tool that keeps evolving. `zbxtemplar` isolates it in a **versioned catalog** (`zbxtemplar.catalog.zabbix_7_4` today), so a Zabbix upgrade is one import swap per module rather than a framework migration, and the core stays stable while new releases are added as sibling `catalog.zabbix_X_Y` subpackages.

Macros follow a layered resolution chain: entity macros → linked template macros → module-level macros → context macros. Module-level macros (`self.add_macro(...)` inside `compose()`) act as the global tier — shared across every template and host in the module and exported as `set_macro` YAML for the executor to apply.

On top of all this, `Context` validates references at generation time — against previously generated or exported YAML. Additionally, the executor applies **fail-fast typo checking** to your `decree` YAML configurations. A typo in a host group name, a missing template, or even misspelling a configuration key (like `expire_at` instead of `expires_at`) halts execution *before* any mutating API calls are made. Deterministic UUIDs prevent import duplicates. Mistakes break against your code, not against production (see [CLI Reference](./doc/cli-reference.md)).

The two module types exist because Zabbix mixes declarative and live-state objects. Templates and hosts fit the native import/export model cleanly; users, SAML, actions, and host encryption need API-driven apply logic. Both outputs stay as plain YAML so the review boundary — the PR diff — is the same in both cases.

## Quick Example

```python
from zbxtemplar.modules import TemplarModule
from zbxtemplar.zabbix import TriggerPriority, TemplateGroup, HostGroup, AgentInterface
from zbxtemplar.catalog.zabbix_7_4 import functions


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

        host = self.add_host("My Server", groups=[HostGroup("Linux Servers")])
        host.link_template(template)
        host.link_interface(AgentInterface(ip="192.168.1.10"))
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

Install:

```bash
pip install .
```

Python 3.11+ is required. The install includes both the generator (`zbxtemplar`) and the executor (`zbxtemplar-exec`).

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
- [`doc/authoring-monitoring.md`](./doc/authoring-monitoring.md) for templates, hosts, items, and the trigger expression builder
- [`doc/authoring-decree.md`](./doc/authoring-decree.md) for users, groups, SAML, host encryption, and tokens
- [`doc/authoring-actions.md`](./doc/authoring-actions.md) for action conditions and operations
- [`doc/cli-reference.md`](./doc/cli-reference.md) for CLI flags, `--param`, `--context`, and module-loading behavior
- [`doc/executor.md`](./doc/executor.md) for apply/decree/scroll usage
- [`doc/security.md`](./doc/security.md) for the operational safety model
- [`doc/decree_reference.md`](./doc/decree_reference.md) for the generated YAML schema reference
- [`doc/reference/`](./doc/reference/README.md) for compact lookup tables, including the trigger function glossary

## Current Scope

Good fit:

- teams that want reviewable monitoring definitions in Python
- repositories where monitoring config should live close to service code
- environments where users, permissions, and alert-routing changes need to be scripted cleanly

Out of scope:

- a generic Zabbix API client — `zbxtemplar` covers the configuration primitives needed for the workflow, not every API endpoint
- a dry-run / diff engine — the safety model is "test environment first, production second" (see [Getting Started — Typical Workflow](./doc/getting-started.md))
- unattended autonomous deployment — the executor is built for reviewed pipelines, not self-healing reconciliation

## License

MIT
