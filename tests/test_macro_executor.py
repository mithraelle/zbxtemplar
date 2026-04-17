from unittest.mock import MagicMock

from zbxtemplar.executor.operations.MacroOperation import MacroOperation
from zbxtemplar.zabbix.macro import Macro


def _macros(*dicts):
    return [Macro.from_dict(d) for d in dicts]


def test_creates_new():
    api = MagicMock()
    api.usermacro.get.return_value = []

    op = MacroOperation(_macros({"name": "SNMP_COMMUNITY", "value": "public"}), api)
    op.execute()
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$SNMP_COMMUNITY}", value="public", type=0
    )


def test_updates_existing():
    api = MagicMock()
    api.usermacro.get.return_value = [
        {"macro": "{$SNMP_COMMUNITY}", "globalmacroid": "42"}
    ]

    op = MacroOperation(_macros({"name": "SNMP_COMMUNITY", "value": "private"}), api)
    op.execute()
    api.usermacro.updateglobal.assert_called_once_with(
        globalmacroid="42", value="private", type=0
    )
    api.usermacro.createglobal.assert_not_called()


def test_secret_type():
    api = MagicMock()
    api.usermacro.get.return_value = []

    op = MacroOperation(_macros({"name": "DB_PASSWORD", "value": "s3cret", "type": "SECRET_TEXT"}), api)
    op.execute()
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$DB_PASSWORD}", value="s3cret", type=1
    )


def test_batch():
    api = MagicMock()
    api.usermacro.get.return_value = [
        {"macro": "{$EXISTING}", "globalmacroid": "10"}
    ]

    op = MacroOperation(_macros(
        {"name": "EXISTING", "value": "updated"},
        {"name": "NEW_ONE", "value": "fresh"},
    ), api)
    op.execute()
    api.usermacro.updateglobal.assert_called_once_with(
        globalmacroid="10", value="updated", type=0
    )
    api.usermacro.createglobal.assert_called_once_with(
        macro="{$NEW_ONE}", value="fresh", type=0
    )
