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

For `DecreeModule`:

- `-o, --output`
- `--user-groups-output`
- `--users-output`
- `--actions-output`

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

Supported top-level keys:

- `zabbix_export`
- `set_macro`
- `user_group`
- `add_user`
- `actions`

The context registry exposes lookups such as:

- `get_macro(name)`
- `get_template_group(name)`
- `get_host_group(name)`
- `get_template(name)`
- `get_host(name)`
- `get_user_group(name)`

Common uses include:

- referencing existing configuration objects by name from exported YAML
- validating module references before apply/import
- composing multi-step generation flows (for example, monitoring output reused by decree generation)

### Notes on context injection

- The loader injects `context` only when the module's `__init__` signature includes a `context` parameter.
- `DecreeModule` and `TemplarModule` base classes accept `context=None`, so subclasses that do not hide it will receive `self.context`.
- If you override `__init__` in `TemplarModule`, include `context=None` and pass it to `super().__init__(context=context)`.

## Output Behavior

### `TemplarModule`

`to_export()` writes a combined `zabbix_export` structure.

`export_templates()` and `export_hosts()` split the content when you want template and host lifecycles to remain separate.

Template and host groups are deduplicated automatically during export.

### `DecreeModule`

`to_export()` merges any defined sections into one decree mapping.

The split export helpers are:

- `export_user_groups()`
- `export_users()`
- `export_actions()`

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
