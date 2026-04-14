from zbxtemplar.dicts.DictEntity import DictEntity, SchemaField


class SuperAdmin(DictEntity):
    _SCHEMA = [
        SchemaField("username", description="New login name for the super admin."),
        SchemaField("password", description="New password."),
        SchemaField("current_password", description="Current password (required when changing password)."),
    ]