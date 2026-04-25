from typing import Self, get_origin

from zbxtemplar.decree import UserGroup, User
from zbxtemplar.decree.Action import Action
from zbxtemplar.decree.Encryption import Encryption, HostEncryption
from zbxtemplar.decree.saml import SamlProvider
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
    """Decree YAML contents: user groups, SAML, users, actions, and host encryption."""

    _SCHEMA = [
        SchemaField("user_group", str_type="list[UserGroup]",
                    description="User group definitions to create or update before users.",
                    type=list[UserGroup]),
        SchemaField("saml", str_type="SamlProvider",
                    description="SAML userdirectory definition to create or update after user groups.",
                    type=SamlProvider),
        SchemaField("add_user", str_type="list[User]",
                    description="User definitions to create or update.",
                    type=list[User]),
        SchemaField("actions", str_type="list[dict]",
                    description="Zabbix action definitions to create or update.",
                    type=list[Action]),
        SchemaField("encryption", str_type="EncryptionDecree | list[EncryptionDecree]",
                    description="Host encryption settings with host_defaults and hosts entries.",
                    type=list[EncryptionDecree]),
    ]

    @classmethod
    def _merge_decree(cls, sources):
        list_keys = {f.key for f in cls._SCHEMA if get_origin(f.type) is list}
        merged = {}
        for src in sources:
            if isinstance(src, str):
                src = cls._load_yaml(src)
            for key, value in src.items():
                if key in list_keys:
                    merged.setdefault(key, []).extend(value if isinstance(value, list) else [value])
                else:
                    if key in merged:
                        raise ValueError(
                            f"Decree: multiple '{key}' entries across merged sources; only one allowed"
                        )
                    merged[key] = value
        return merged

    @classmethod
    def from_data(cls, data) -> Self:
        if isinstance(data, str):
            data = cls._load_yaml(data)
        if isinstance(data, list):
            data = cls._merge_decree(data)
        if isinstance(data, dict) and isinstance(data.get("encryption"), dict):
            data = {**data, "encryption": [data["encryption"]]}
        return cls.from_dict(data)
