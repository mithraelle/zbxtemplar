from typing import Self

from zbxtemplar.decree.Token import Token
from zbxtemplar.dicts.Decree import Decree
from zbxtemplar.dicts.Schema import Schema, field
from zbxtemplar.zabbix.macro import Macro


class SuperAdmin(Schema):
    """Super admin credentials update for the authenticated user."""

    username: str | None = field(
        description="New login name for the super admin.",
    )
    password: str | None = field(
        description="New password.",
    )
    current_password: str | None = field(
        description="Current password (required when changing password).",
    )


class UserToken(Schema):
    """API token for an existing Zabbix user. The user itself is not created or changed."""

    username: str = field(
        optional=False,
        description="Existing Zabbix username that owns the token.",
    )
    token: Token = field(
        optional=False,
        str_type="Token",
        description="API token provisioning configuration.",
    )
    force_token: bool | None = field(
        str_type="bool",
        description="Update and re-generate an existing token with the same name.",
    )


class Scroll(Schema):
    """Ordered deployment scroll: bootstrap, global macros, imports, decree, and tokens."""

    set_super_admin: SuperAdmin | None = field(
        str_type="SuperAdmin",
        description="Super admin update — password and/or username. Requires current_password when changing password.",
    )
    set_macro: list[Macro] | None = field(
        str_type="list[Macro]",
        description="Global macro definition, list of definitions, or path to a macro YAML file.",
    )
    apply: list[str] | None = field(
        str_type="str | list[str]",
        description="Zabbix-native YAML file path or paths to import.",
    )
    decree: Decree | None = field(
        str_type="Decree",
        description="Inline decree data, merged decree data list, or decree YAML path.",
    )
    set_token: list[UserToken] | None = field(
        str_type="list[UserToken]",
        description="API tokens to issue for existing users. Runs after decree.",
    )

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