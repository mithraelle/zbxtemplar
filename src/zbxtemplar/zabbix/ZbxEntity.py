from typing import Any
from enum import Enum, StrEnum
import uuid

from zbxtemplar.zabbix.macro import MacroType


class YesNo(StrEnum):
    NO = "NO"
    YES = "YES"


MacroType._API_VALUES = {"TEXT": 0, "SECRET_TEXT": 1, "VAULT": 2}

ZBX_TEMPLAR_NAMESPACE = "Zbx Templar"
_NAMESPACE_UUID = uuid.uuid5(uuid.NAMESPACE_DNS, ZBX_TEMPLAR_NAMESPACE)

def set_uuid_namespace(namespace: str):
    """Set the namespace string used for deterministic UUID generation.

    Call once before creating any entities if you need a custom namespace.
    Defaults to "Zbx Templar".
    """
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
    def __init__(self, name: str, uuid_seed: str | None = None):
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
        self.tags: dict[str, Tag] = {}

    def add_tag(self, tag: str, value: str = ""):
        self.tags[tag] = Tag(name=tag, value=value)
        return self

    def tags_to_list(self):
        return [t.to_dict() for t in self.tags.values()]

    def load_tags(self, tags: dict[str, str]):
        """Load tags from a dict.

        Args:
            tags: Mapping of tag name to value.
                Example: ``{"Application": "CPU", "Component": "OS"}``
        """
        for tag, value in tags.items():
            self.add_tag(tag, value)
        return self


class WithGroups():
    def __init__(self):
        super().__init__()
        self.groups: list[ZbxEntity] = []

    def add_group(self, group: ZbxEntity):
        if any(g.name == group.name for g in self.groups):
            raise ValueError(
                f"Duplicate group '{group.name}' on '{getattr(self, 'name', type(self).__name__)}'"
            )
        self.groups.append(group)
        return self

    def groups_to_list(self):
        return [{"name": g.name} for g in self.groups]
