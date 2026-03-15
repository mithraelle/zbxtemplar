from typing import Any, List, Optional, Dict, Union
from enum import Enum
import uuid

class YesNo(str, Enum):
    NO = "NO"
    YES = "YES"

ZBX_TEMPLAR_NAMESPACE = "Zbx Templar"
_NAMESPACE_UUID = uuid.uuid5(uuid.NAMESPACE_DNS, ZBX_TEMPLAR_NAMESPACE)

def set_uuid_namespace(namespace: str):
    global ZBX_TEMPLAR_NAMESPACE, _NAMESPACE_UUID
    ZBX_TEMPLAR_NAMESPACE = namespace
    _NAMESPACE_UUID = uuid.uuid5(uuid.NAMESPACE_DNS, namespace)

def _make_uuid(seed: str) -> str:
    """Deterministic UUID from seed, masked as UUIDv4. Zabbix rejects UUID5 on import."""
    h = uuid.uuid5(_NAMESPACE_UUID, seed).hex
    return h[:12] + '4' + h[13:16] + hex(0x8 | (int(h[16], 16) & 0x3))[2:] + h[17:]

def _serialize(value, skip_uuid=False):
    if hasattr(value, 'to_dict'):
        try:
            return value.to_dict(skip_uuid=skip_uuid)
        except TypeError:
            return value.to_dict()
    if isinstance(value, dict):
        return {k: _serialize(v, skip_uuid) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v, skip_uuid) for v in value]
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool)):
        return {k: _serialize(v, skip_uuid) for k, v in value.__dict__.items()}
    return value

class ZbxEntity:
    def __init__(self, name: str, uuid_seed: str = None):
        super().__init__()
        self.name = name
        self.uuid = _make_uuid(uuid_seed or name)

    def to_dict(self, skip_uuid=False) -> dict[str, Any]:
        # Attributes starting with _ are internal-only (e.g. _host) and skipped here
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            if skip_uuid and key == 'uuid':
                continue
            if value is None or value == {} or value == []:
                continue
            list_method = getattr(self, f'{key}_to_list', None)
            if list_method:
                result[key] = list_method()
            else:
                result[key] = _serialize(value, skip_uuid)
        return result

class Tag:
    def __init__(self, name: str, value: str = ""):
        self.name = name
        self.value = value

    def to_dict(self):
        return {"tag": self.name, "value": self.value}

class WithTags():
    def __init__(self):
        super().__init__()
        self.tags: Dict[str, Tag] = {}

    def add_tag(self, tag: str, value: str = ""):
        self.tags[tag] = Tag(name=tag, value=value)
        return self

    def tags_to_list(self):
        return [t.to_dict() for t in self.tags.values()]

    def load_tags(self, tags: Dict[str, str]):
        """Load tags from a dict.

        Args:
            tags: Mapping of tag name to value.
                Example: ``{"Application": "CPU", "Component": "OS"}``
        """
        for tag, value in tags.items():
            self.add_tag(tag, value)
        return self

class Macro():
    def __init__(self, name: str, value: str, description: Optional[str] = None):
        self.name = name
        self.value = value
        self.description = description

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
        result = {"macro": self.full_name, "value": self.value}
        if self.description is not None:
            result["description"] = self.description
        return result

class WithMacros():
    def __init__(self):
        super().__init__()
        self.macros: Dict[str, Macro] = {}

    def add_macro(self, name: str, value: Union[str, int], description: Union[str, None] = None):
        clean_name = name.replace("{$", "").replace("}", "")
        self.macros[clean_name] = Macro(name=clean_name, value=str(value), description=description)
        return self

    def load_macros(self, macros: Union[Dict[str, Union[str, tuple]], List[dict]]):
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

    def get_macro(self, name: str) -> Macro:
        clean_name = name.replace("{$", "").replace("}", "")
        macro = self.macros.get(clean_name)
        if macro is None:
            raise KeyError(f"Macro '{{${clean_name}}}' not found on '{self.name}'")
        return macro



class WithGroups():
    def __init__(self):
        super().__init__()
        self.groups: List[ZbxEntity] = []

    def add_group(self, group: ZbxEntity):
        if not any(g.name == group.name for g in self.groups):
            self.groups.append(group)
        return self

    def groups_to_list(self):
        return [{"name": g.name} for g in self.groups]

