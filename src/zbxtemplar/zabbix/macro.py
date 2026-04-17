from dataclasses import dataclass
from enum import StrEnum

from zbxtemplar.dicts.DictEntity import DictEntity, SchemaField


class MacroType(StrEnum):
    """Macro types (Zabbix export values)."""
    TEXT = "TEXT"
    SECRET_TEXT = "SECRET_TEXT"
    SECRET = "SECRET_TEXT"
    VAULT = "VAULT"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val = value.upper()
            if val == "SECRET":
                val = "SECRET_TEXT"
            for member in cls:
                if member.value == val:
                    return member
        return super()._missing_(value)


@dataclass(frozen=True)
class Macro(DictEntity):
    _SCHEMA = [
        SchemaField("name", optional=False, description="Macro name without {$...} braces.", type=str),
        SchemaField("value", optional=False, description="Macro value.", type=str),
        SchemaField("description", description="Optional macro description.", type=str),
        SchemaField("type", str_type="MacroType", description="Macro type: TEXT, SECRET_TEXT, SECRET, or VAULT.", type=MacroType),
    ]

    name: str
    value: str
    description: str | None = None
    type: MacroType = MacroType.TEXT

    @property
    def full_name(self) -> str:
        return f"{{${self.name}}}"

    def __str__(self):
        return self.full_name

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    def to_dict(self):
        result = {"macro": self.full_name, "type": self.type.value, "value": self.value}
        if self.description is not None:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, data: dict):
        if "macro" in data:
            name = data["macro"].replace("{$", "").replace("}", "")
        else:
            name = data["name"]
        raw_type = data.get("type", MacroType.TEXT)
        return cls(
            name=name,
            value=data.get("value", ""),
            description=data.get("description"),
            type=MacroType(raw_type),
        )


class WithMacros():
    _lookup: dict[str, Macro] = {}
    _context: dict[str, Macro] = {}

    def __init__(self):
        super().__init__()
        self.macros: dict[str, Macro] = {}

    def add_macro(self, name: str, value: str | int, description: str | None = None, type: MacroType = MacroType.TEXT) -> Macro:
        clean_name = name.replace("{$", "").replace("}", "")
        self.macros[clean_name] = Macro(name=clean_name, value=str(value), description=description, type=type)
        return self.macros[clean_name]

    def load_macros(self, macros: dict[str, str | tuple] | list[dict]):
        """Load macros from a dict or a list of dicts.

        Accepts two formats:

        **Dict** — for programmatic use::

            load_macros({"TIMEOUT": "30"})
            load_macros({"TIMEOUT": ("30", "Connection timeout")})

        **List of dicts** — for data loaded from YAML/XML::

            load_macros([
                {"name": "TIMEOUT", "value": "30", "description": "Connection timeout"}
            ])

        Args:
            macros: Either a ``{name: value}`` / ``{name: (value, description)}`` dict,
                or a list of dicts with ``name``, ``value``, and optional ``description`` keys.
        """
        if isinstance(macros, dict):
            for name, value in macros.items():
                if isinstance(value, tuple):
                    self.add_macro(name, value[0], value[1] if len(value) > 1 else None)
                else:
                    self.add_macro(name, value)
        else:
            for entry in macros:
                self.add_macro(entry["name"], entry["value"], entry.get("description"))
        return self

    def macros_to_list(self):
        return [m.to_dict() for m in self.macros.values()]

    def get_macro(self, name: str):
        clean_name = name.replace("{$", "").replace("}", "")
        macro = self.macros.get(clean_name)
        if macro is not None:
            return macro

        templates = getattr(self, "templates", None)
        if templates:
            for t in templates:
                macro = t.get_macro(name)
                if macro is not None:
                    return macro

        macro = self._lookup.get(clean_name)
        if macro is not None:
            return macro
        macro = self._context.get(clean_name)
        if macro is not None:
            return macro

        owner_name = getattr(self, "name", None)
        if owner_name is None:
            tag = "registry"
        else:
            tag = f"{type(self).__name__.lower()} '{owner_name}'"
            if templates is not None:
                tag += " or its linked templates"
        raise KeyError(f"Macro '{{${clean_name}}}' not found on {tag}")
