import difflib
import builtins
import os
import re
from dataclasses import dataclass
from enum import Enum
from types import GenericAlias, UnionType
from typing import Self, TypeAlias, get_args, get_origin

import yaml


SchemaRuntimeType: TypeAlias = builtins.type | GenericAlias | UnionType


@dataclass
class SchemaField:
    key: str
    optional: bool = True
    str_type: str = "str"
    description: str = ""
    type: SchemaRuntimeType | None = None
    property: str | None = None


class DictEntity:
    _SCHEMA: list[SchemaField] = []

    _base_dir: str = None
    _resolve_envs: bool = False

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

        return obj

    @classmethod
    def from_data(cls, data: dict | list | str) -> Self:
        if isinstance(data, dict):
            return cls.from_dict(data)
        raise NotImplementedError()

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
                f"Pre-flight check failed. Missing environment variables:\n{lines}\n\n"
                "Execution aborted. No changes were made."
            )
        return result
