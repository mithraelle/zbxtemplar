import difflib
import builtins
import os
import re
from dataclasses import dataclass
from enum import Enum, StrEnum
from types import GenericAlias, UnionType
from typing import Self, TypeAlias, get_args, get_origin

import yaml

SchemaRuntimeType: TypeAlias = builtins.type | GenericAlias | UnionType


class ApiStrEnum(StrEnum):
    """StrEnum whose members carry a Zabbix API integer via `.api`. Declare members as `NAME = "NAME", <int>`.

    Also accepts the api integer (as int or str) for construction, e.g. ``Permission("2") is Permission.READ``.
    """
    api: int

    def __new__(cls, value: str, api: int):
        member = str.__new__(cls, value)
        member._value_ = value
        member.api = api
        return member

    @classmethod
    def _missing_(cls, value):
        try:
            api_int = int(value)
        except (TypeError, ValueError):
            return None
        for member in cls:
            if member.api == api_int:
                return member
        return None


@dataclass
class SchemaField:
    key: str
    optional: bool = True
    str_type: str = "str"
    description: str = ""
    type: SchemaRuntimeType | None = None
    property: str | None = None
    api_key: str | None = None


class Schema:
    _SCHEMA: list[SchemaField] = []

    _base_dir: str = None
    _resolve_envs: bool = False

    def to_dict(self) -> dict:
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            if value is None or value == {} or value == []:
                continue
            list_method = getattr(self, f'{key}_to_list', None)
            if list_method:
                items = list_method()
                if items:
                    result[key] = items
                continue
            serialized = self._serialize(value, key)
            if serialized == {} or serialized == []:
                continue
            result[key] = serialized
        return result

    def _serialize(self, value, key):
        if hasattr(value, 'to_dict'):
            return value.to_dict()
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, list):
            return [self._serialize(v, key) for v in value]
        if isinstance(value, (str, int, float, bool)):
            return value
        if type(value).__str__ is not object.__str__:
            return str(value)
        raise TypeError(
            f"{type(self).__name__}.to_dict: cannot serialize "
            f"{key}={value!r} ({type(value).__name__})"
        )

    @classmethod
    def validate(cls, data: dict) -> bool:
        if not isinstance(data, dict):
            raise ValueError(f"{cls.__name__}: expected a mapping, got {type(data).__name__}")
        if not cls._SCHEMA:
            return True

        all_keys = {f.key for f in cls._SCHEMA}
        required_keys = {f.key for f in cls._SCHEMA if not f.optional}

        unknown = set(data) - all_keys
        if unknown:
            key = sorted(unknown)[0]
            suggestion = difflib.get_close_matches(key, all_keys, n=1)
            hint = f", did you mean '{suggestion[0]}'?" if suggestion else ""
            raise ValueError(f"{cls.__name__}: unknown key '{key}'{hint}")

        missing = required_keys - set(data)
        if missing:
            raise ValueError(
                f"{cls.__name__}: missing required key(s): {', '.join(sorted(missing))}"
            )

        empty = {k for k in required_keys if data[k] is None or data[k] == ""}
        if empty:
            raise ValueError(
                f"{cls.__name__}: required key(s) must not be empty: {', '.join(sorted(empty))}"
            )

        return True

    @classmethod
    def _resolve_path(cls, path):
        if cls._base_dir and not os.path.isabs(path):
            return os.path.join(cls._base_dir, path)
        return path

    @classmethod
    def _load_yaml(cls, path):
        resolved_path = cls._resolve_path(path)
        try:
            with open(resolved_path) as f:
                raw = f.read()
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse '{resolved_path}': {e}") from e
        if cls._resolve_envs:
            return cls._resolve_env(data)
        return data

    @classmethod
    def from_file(cls, path) -> Self:
        data = cls._load_yaml(path)
        return cls.from_data(data)

    @classmethod
    def _resolve_type(cls, value_type: SchemaRuntimeType, value):
        origin = get_origin(value_type)
        args = get_args(value_type)

        if origin is list:
            item_type = args[0] if args else None
            if (
                isinstance(item_type, type)
                and issubclass(item_type, ApiStrEnum)
                and not isinstance(value, list)
            ):
                try:
                    mask = int(value)
                except (TypeError, ValueError):
                    pass
                else:
                    return [m for m in item_type if mask & m.api]
            if (
                isinstance(value, str)
                and isinstance(item_type, type)
                and issubclass(item_type, Enum)
            ):
                value = [v.strip() for v in value.split(",") if v.strip()]
            if not isinstance(value, list):
                raise ValueError(f"expected list, got {type(value).__name__}")
            if not args:
                return value
            return [cls._resolve_type(item_type, item) for item in value]

        if origin is dict:
            if not isinstance(value, dict):
                raise ValueError(f"expected dict, got {type(value).__name__}")
            return value

        if isinstance(value_type, UnionType):
            errors = []
            for option_type in args:
                try:
                    return cls._resolve_type(option_type, value)
                except (TypeError, ValueError) as e:
                    errors.append(str(e))
            raise ValueError(
                f"expected one of {value_type}, got {type(value).__name__}: "
                + "; ".join(errors)
            )

        if value_type in (str, int, float, bool, dict, list):
            if not isinstance(value, value_type):
                raise ValueError(f"expected {value_type.__name__}, got {type(value).__name__}")
            return value

        if isinstance(value_type, type) and issubclass(value_type, Enum):
            if isinstance(value, value_type):
                return value
            if isinstance(value, str) and value in value_type.__members__:
                return value_type[value]
            if isinstance(value, str) and issubclass(value_type, int):
                try:
                    value = int(value)
                except ValueError:
                    pass
            try:
                return value_type(value)
            except ValueError as e:
                raise ValueError(
                    f"expected {value_type.__name__}, got {value!r}"
                ) from e

        if hasattr(value_type, "from_data"):
            return value_type.from_data(value)
        if hasattr(value_type, "from_dict") and isinstance(value, dict):
            return value_type.from_dict(value)
        if isinstance(value, value_type):
            return value
        raise ValueError(f"expected {value_type.__name__}, got {type(value).__name__}")

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        cls.validate(data)
        obj = cls.__new__(cls)

        for field in cls._SCHEMA:
            property_name = field.property if field.property else field.key
            if field.key in data:
                field_data = data[field.key]
                if field.type:
                    try:
                        field_data = cls._resolve_type(field.type, field_data)
                    except (TypeError, ValueError) as e:
                        raise ValueError(f"{cls.__name__}.{field.key}: {e}") from e

                setattr(obj, property_name, field_data)
            else:
                setattr(obj, property_name, None)

        obj._wire_up()
        return obj

    def _wire_up(self) -> None:
        pass

    @classmethod
    def from_data(cls, data: dict | list | str) -> Self:
        if isinstance(data, dict):
            return cls.from_dict(data)
        raise NotImplementedError()

    @classmethod
    def from_api(cls, data: dict) -> Self:
        """Build an instance from a raw Zabbix API payload: recursively strip unknown keys and apply ``api_key`` renames."""
        return cls.from_data(cls._strip_api(data))

    @classmethod
    def _strip_api(cls, data: dict) -> dict:
        payload = {}
        for field in cls._SCHEMA:
            src_key = field.api_key or field.key
            if src_key not in data:
                continue
            payload[field.key] = cls._strip_api_value(field.type, data[src_key])
        return payload

    @staticmethod
    def _strip_api_value(field_type, value):
        if value is None or field_type is None:
            return value
        if isinstance(field_type, type) and issubclass(field_type, Schema):
            if isinstance(value, dict):
                return field_type._strip_api(value)
            return value
        if get_origin(field_type) is list and isinstance(value, list):
            args = get_args(field_type)
            if args and isinstance(args[0], type) and issubclass(args[0], Schema):
                inner = args[0]
                return [inner._strip_api(v) if isinstance(v, dict) else v for v in value]
        return value

    @staticmethod
    def _resolve_env(obj):
        missing = set()

        def replace(match):
            var = match.group(1)
            env_val = os.environ.get(var)
            if env_val is None:
                missing.add(var)
                return ""
            return env_val

        def walk(o):
            if isinstance(o, str):
                return re.sub(r'\$\{(\w+)\}', replace, o)
            if isinstance(o, dict):
                return {k: walk(v) for k, v in o.items()}
            if isinstance(o, list):
                return [walk(v) for v in o]
            return o

        result = walk(obj)
        if missing:
            lines = "\n".join(f"  {var}" for var in sorted(missing))
            raise ValueError(
                f"Missing environment variable(s):\n{lines}"
            )
        return result

    @classmethod
    def detect_type(cls, filename: str) -> type:
        from zbxtemplar.dicts.ZabbixExport import ZabbixExport
        from zbxtemplar.dicts.Scroll import Scroll
        from zbxtemplar.dicts.Decree import Decree
        path = os.path.abspath(filename)
        with open(path) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"{filename}: expected a YAML mapping, got {type(data).__name__}")

        if "zabbix_export" in data:
            inner = data["zabbix_export"]
            if isinstance(inner, dict) and {"hosts", "templates"} & set(inner):
                return ZabbixExport

        keys = set(data)
        for entity_cls in [Scroll, Decree]:
            if keys & {f.key for f in entity_cls._SCHEMA}:
                return entity_cls

        raise ValueError(
            f"{filename}: unknown format (top-level keys: {', '.join(sorted(keys))})"
        )
