from zbxtemplar.dicts.DictEntity import DictEntity, SchemaField


class Scroll(DictEntity):
    _SCHEMA = [
        SchemaField("set_super_admin", str_type="dict", description="Super admin update — password and/or username. Requires current_password when changing password."),
        SchemaField("set_macro", str_type="str | dict | list", description="Global macro definition, list of definitions, or path to a macro YAML file."),
        SchemaField("apply", str_type="str | list[str]", description="Zabbix-native YAML file path or paths to import."),
        SchemaField("decree", str_type="dict | list | str", description="Inline decree data, merged decree data list, or decree YAML path."),
    ]