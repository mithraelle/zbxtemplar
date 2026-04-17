# Generator Guide

## Purpose

`zbxtemplar` loads Python modules, instantiates `TemplarModule` and `DecreeModule` subclasses, and writes YAML artifacts.

The generator does not call the Zabbix API.

## CLI

```bash
zbxtemplar MODULE.py [outputs...]
```

At least one output flag is required.

### Output flags

For `TemplarModule`:

- `-o, --output`
- `--templates-output`
- `--hosts-output`
- `--macros-output` — required if module-level macros are defined (see [Macro Resolution](#macro-resolution))

For `DecreeModule`:

- `-o, --output`
- `--user-groups-output`
- `--users-output`
- `--actions-output`
- `--encryption-output`
- `--macros-output` — optional; module-level macros are already included in `-o` output

### Other flags

- `--namespace` sets the UUID namespace for deterministic IDs
- `--param KEY=VALUE` passes constructor parameters
- `--context FILE` loads one or more context YAML files

## Module Discovery

The loader imports the given Python file and scans it for subclasses of:

- `TemplarModule`
- `DecreeModule`

Every discovered subclass is instantiated and exported.

If a file defines multiple module classes, each one is processed.

## Constructor Parameters

The constructor is the module contract.

Example:

```python
class MyModule(TemplarModule):
    def __init__(self, env: str = "dev", threshold: int = 5):
        super().__init__()
```

Pass values from the CLI:

```bash
zbxtemplar my_module.py -o out.yml \
  --param env=prod \
  --param threshold=10
```

Current coercion is based on type annotations:

- `str`
- `int`
- `float`
- `bool`

If a required parameter is missing or an unknown parameter is supplied, generation fails with a `TypeError`.

## Context Files

`--context` is accepted by the CLI for any generation run. During loading, the generator forwards the built `Context` into module constructors that accept a `context` parameter.

Context serves two practical roles:

### 1. Validating Against Existing Configuration

Context can load exported or otherwise prepared YAML that represents an already existing environment. This lets generation validate references against a known baseline — not only objects created in the same run:

```bash
# Export existing config from Zabbix, then use it as context for new modules
zbxtemplar new_decree.py -o decree.yml --context existing_templates.yml
```

A typo like `self.context.get_host_group("Prodction")` raises `ValueError` during generation — before any YAML is produced, before any API call happens.

### 2. Composing Multi-Step Generation

Previously generated artifacts provide the registry that new module code builds on:

```bash
zbxtemplar monitoring.py --templates-output templates.yml
zbxtemplar decree.py -o decree.yml --context templates.yml
```

The decree module can reference templates and groups from the monitoring output by name, with validation.

### What Context validates

The registry exposes typed lookups that raise `ValueError` when the name is not found:

- `get_macro(name)`
- `get_template_group(name)`
- `get_host_group(name)`
- `get_template(name)`
- `get_host(name)`
- `get_user_group(name)`

These load rich domain objects, not plain name strings — so the returned template has its items, triggers, and groups available for inspection.

### What Context does not validate

Context is a snapshot, not a live connection. It cannot prove:

- that the live Zabbix instance has not changed since the YAML snapshot was made
- that every apply-time API call will succeed
- that all runtime concerns are modeled in the context registry

The honest framing: generation-time validation catches typos and missing references within the scope of supplied YAML. Apply-time resolution (executor resolving names to live Zabbix IDs) catches the rest. Together they form a two-stage safety net where the cheapest failures happen first.

### Supported context YAML formats

- `zabbix_export` — Zabbix-native YAML (templates, hosts, groups)
- `set_macro` — global macros
- `user_group` — user groups
- `add_user` — users

Multiple `--context` flags accumulate into one registry. Unknown formats are rejected with an error.

### Notes on context injection

- The loader builds context once for the module run.
- `DecreeModule` and `TemplarModule` expose it as `self.context`.
- Module constructors do not need a `context` parameter.

## Macro Resolution

`get_macro(name)` walks a fixed resolution chain in order:

1. **Entity macros** — macros defined directly on the template or host (`entity.add_macro(...)`)
2. **Linked template macros** — macros on templates linked to the current entity
3. **Module macros** — macros defined on the module itself (`self.add_macro(...)` inside `__init__`)
4. **Context macros** — macros loaded from `--context` files in `set_macro` format

A `KeyError` is raised if the name is not found at any level.

Module-level macros are the "global" tier — shared across every template and host in the module. Since Zabbix has no native import format for global macros, `TemplarModule` writes them as `set_macro` YAML via `--macros-output`. The executor applies them to the live instance via `usermacro.createglobal` / `usermacro.updateglobal`.

`add_macro()` returns the `Macro` object, so you can capture it and use it directly without a separate `get_macro()` call:

```python
threshold = self.add_macro("THRESHOLD", 90, "Alert threshold")
item.add_trigger("High CPU", "last", ">", threshold, ...)
```

## Output Behavior

### `TemplarModule`

`to_export()` writes a combined `zabbix_export` structure.

`export_templates()` and `export_hosts()` split the content when you want template and host lifecycles to remain separate.

Template and host groups are deduplicated automatically during export.

### `DecreeModule`

`to_export()` merges any defined sections into one decree mapping, including module-level macros if any are defined.

The split export helpers are:

- `export_macros()`
- `export_user_groups()`
- `export_users()`
- `export_actions()`
- `export_encryption()`

## Programmatic Loading

The public loader lives in `zbxtemplar.main`:

```python
from zbxtemplar.main import load_module

modules = load_module("path/to/module.py", params={"env": "prod"})

for name, module in modules.items():
    print(name, module.to_export())
```

## Practical Guidance

- Keep module logic in `__init__`; that is the supported contract.
- Use `--templates-output` and `--hosts-output` when inventory and reusable templates have different change flows.
- Load exported YAML (generated artifacts or existing-instance exports) via `--context` when your module needs stable name-based references.
- Prefer typed objects first; use raw dicts and raw strings only as escape hatches.
