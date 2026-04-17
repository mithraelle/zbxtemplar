from typing import Self

from zbxtemplar.dicts.Decree import Decree
from zbxtemplar.dicts.Schema import Schema, SchemaField
from zbxtemplar.zabbix.macro import Macro


class SuperAdmin(Schema):
    _SCHEMA = [
        SchemaField("username", description="New login name for the super admin."),
        SchemaField("password", description="New password."),
        SchemaField("current_password", description="Current password (required when changing password)."),
    ]


class Scroll(Schema):
    _SCHEMA = [
        SchemaField("set_super_admin", str_type="SuperAdmin", type=SuperAdmin,
                    description="Super admin update — password and/or username. Requires current_password when changing password."),
        SchemaField("set_macro", str_type="list[Macro]", type=list[Macro],
                    description="Global macro definition, list of definitions, or path to a macro YAML file."),
        SchemaField("apply", str_type="str | list[str]", type=list[str],
                    description="Zabbix-native YAML file path or paths to import."),
        SchemaField("decree", str_type="Decree", type=Decree,
                    description="Inline decree data, merged decree data list, or decree YAML path."),
    ]

    @classmethod
    def _load_macros_from_file(cls, path):
        data = cls._load_yaml(path)
        if isinstance(data, dict) and "set_macro" in data:
            data = data["set_macro"]
        return data if isinstance(data, list) else [data]

    @classmethod
    def _resolve_macro(cls, data) -> list[dict]:
        raw = data if isinstance(data, list) else [data]
        flat = []
        for item in raw:
            if isinstance(item, str):
                flat.extend(cls._load_macros_from_file(item))
            else:
                flat.append(item)
        return flat

    @classmethod
    def from_data(cls, data) -> Self:
        if not isinstance(data, dict):
            raise ValueError(f"{cls.__name__}: expected a mapping, got {type(data).__name__}")
        data = dict(data)
        if data.get("set_macro") is not None:
            data["set_macro"] = cls._resolve_macro(data["set_macro"])
        return cls.from_dict(data)
