# Modules & Context

Cheat sheet. CLI flag semantics live in [CLI Reference](../cli-reference.md).

## Entry points

```python
from zbxtemplar.modules import TemplarModule, DecreeModule
from zbxtemplar.zabbix import MacroType   # for module-level macros
```

Subclass one, implement `compose()`. The CLI auto-detects the base class.

```python
class MyTemplates(TemplarModule):
    def compose(self, env: str = "prod"):
        ...

class MyDecree(DecreeModule):
    def compose(self, alert_email: str = "alerts@example.com"):
        ...
```

`compose()` signature is the `--param KEY=VALUE` surface. Coercion: `int`, `float`, `bool` (`true`/`1`/`yes`); `str` / unannotated pass through. Defaults apply when `--param` is omitted.

## Module-level macros

`TemplarModule` and `DecreeModule` both support `add_macro()`. Emitted as `set_macro` entries; applied as Zabbix global macros.

```python
self.add_macro("MY_MACRO", "value", "description")
self.add_macro("DB_PASSWORD", "${ZBX_DB_PASSWORD}", "DB password", MacroType.SECRET_TEXT)
val = self.get_macro("MY_MACRO")  # Macro object; .value is the string
```

## Context

`self.context` is populated before `compose()` from `--context FILE` (repeatable; accepts Zabbix export and decree YAML). All lookups raise `ValueError` on missing name.

```python
self.context.get_host_group("Linux servers")        # → HostGroup
self.context.get_template_group("My Templates")     # → TemplateGroup
self.context.get_template("My Template")            # → Template
self.context.get_host("my-host")                    # → Host
self.context.get_macro("GLOBAL_MACRO")              # → Macro
self.context.get_user_group("Ops Team")             # → UserGroup
```
