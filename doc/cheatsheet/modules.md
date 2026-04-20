# Modules & Context

## Entry points

```python
from zbxtemplar.modules import TemplarModule, DecreeModule
from zbxtemplar.zabbix import MacroType   # for module-level macros
```

Subclass one, implement `compose()`. The CLI auto-detects the base class and runs it.

```python
class MyTemplates(TemplarModule):
    def compose(self, env: str = "prod"):
        ...

class MyDecree(DecreeModule):
    def compose(self, alert_email: str = "alerts@example.com"):
        ...
```

## CLI

`--param KEY=VALUE` maps to `compose()` parameters by name. Values are coerced based on the parameter's type annotation: `int`, `float`, and `bool` (`true`/`1`/`yes`) are converted; `str` and unannotated parameters receive the value as-is.
Default values in the signature are used when `--param` is omitted.

```bash
zbxtemplar module.py -o output.yml
zbxtemplar module.py -o output.yml --param env=staging
zbxtemplar decree.py -o decree.yml --context templates.yml --param alert_email=ops@co.com
```

Output flags: `-o` (combined), `--templates-output`, `--hosts-output`,
`--user-groups-output`, `--users-output`, `--actions-output`.

`--context FILE` (repeatable) — loads YAML files into `self.context`. Accepts
Zabbix export YAML, decree YAML, or any combination.

## Module-level macros

Both `TemplarModule` and `DecreeModule` support global macros via `add_macro()`.
These are emitted as `set_macro` entries in the output YAML and applied as Zabbix global macros.

```python
self.add_macro("MY_MACRO", "value", "description")
self.add_macro("DB_PASSWORD", "${ZBX_DB_PASSWORD}", "DB password", MacroType.SECRET_TEXT)
val = self.get_macro("MY_MACRO")  # Macro object; .value is the string
```

## Context (DecreeModule)

`self.context` is populated before `compose()` from `--context` files.
All methods raise `ValueError` if the name is not found.

```python
self.context.get_host_group("Linux servers")        # → HostGroup
self.context.get_template_group("My Templates")     # → TemplateGroup
self.context.get_template("My Template")            # → Template
self.context.get_host("my-host")                    # → Host
self.context.get_macro("GLOBAL_MACRO")              # → Macro
self.context.get_user_group("Ops Team")             # → UserGroup
```