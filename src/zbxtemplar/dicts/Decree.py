from typing import Self

from zbxtemplar.decree import UserGroup, User
from zbxtemplar.decree.Action import Action
from zbxtemplar.decree.Encryption import Encryption, HostEncryption
from zbxtemplar.dicts.Schema import Schema, SchemaField


class EncryptionDecree(Schema):
    """Host encryption block: shared host_defaults plus per-host entries."""

    _SCHEMA = [
        SchemaField("host_defaults", str_type="Encryption",
                    description="Default encryption settings merged into each host entry.",
                    type=Encryption),
        SchemaField("hosts", optional=False, str_type="list[HostEncryption]",
                    description="Per-host encryption settings to apply.",
                    type=list[HostEncryption]),
    ]

class Decree(Schema):
    """Decree YAML contents: user groups, users, actions, and host encryption."""

    _SCHEMA = [
        SchemaField("user_group", str_type="list[UserGroup]",
                    description="User group definitions to create or update before users.",
                    type=list[UserGroup]),
        SchemaField("add_user", str_type="list[User]",
                    description="User definitions to create or update.",
                    type=list[User]),
        SchemaField("actions", str_type="list[dict]",
                    description="Zabbix action definitions to create or update.",
                    type=list[Action]),
        SchemaField("encryption", str_type="list[EncryptionDecree]",
                    description="Host encryption settings with host_defaults and hosts entries.",
                    type=list[EncryptionDecree]),
    ]

    @classmethod
    def _merge_decree(cls, sources):
        merged = {}
        for src in sources:
            if isinstance(src, str):
                src = cls._load_yaml(src)
            for key in src:
                merged.setdefault(key, []).extend(
                    src[key] if isinstance(src[key], list) else [src[key]]
                )
        return merged

    @classmethod
    def from_data(cls, data) -> Self:
        if isinstance(data, str):
            data = cls._load_yaml(data)
        if isinstance(data, list):
            data = cls._merge_decree(data)
        return cls.from_dict(data)
