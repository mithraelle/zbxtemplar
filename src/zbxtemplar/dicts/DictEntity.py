import difflib
from dataclasses import dataclass


@dataclass
class SchemaField:
    key: str
    optional: bool = True
    str_type: str = "str"
    description: str = ""


class DictEntity:
    _SCHEMA: list[SchemaField] = []


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
