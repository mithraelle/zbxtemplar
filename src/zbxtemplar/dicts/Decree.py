from zbxtemplar.dicts.DictEntity import DictEntity, SchemaField


class Decree(DictEntity):
    _SCHEMA = [
        SchemaField("user_group", str_type="list[UserGroup]", description="User group definitions to create or update before users."),
        SchemaField("add_user", str_type="list[User]", description="User definitions to create or update."),
        SchemaField("actions", str_type="list[dict]", description="Zabbix action definitions to create or update."),
        SchemaField("encryption", str_type="dict | list[dict]", description="Host encryption settings with host_defaults and hosts entries."),
    ]