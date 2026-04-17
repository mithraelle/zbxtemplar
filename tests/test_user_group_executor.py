from unittest.mock import MagicMock

import pytest

from zbxtemplar.executor.operations.UserGroupOperation import UserGroupOperation
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.decree import UserGroup
from zabbix_utils import APIRequestError


def _api(existing_ugroups=None):
    api = MagicMock()
    api.hostgroup.get.return_value = [
        {"groupid": "2", "name": "Linux servers"},
        {"groupid": "3", "name": "Virtual machines"},
    ]
    api.templategroup.get.return_value = [
        {"groupid": "10", "name": "Test Template"},
    ]
    api.usergroup.get.return_value = (
        [{"usrgrpid": g["usrgrpid"], "name": g["name"]} for g in existing_ugroups]
        if existing_ugroups else []
    )
    return api


def _groups(*dicts):
    return [UserGroup.from_dict(d) for d in dicts]


def test_creates_user_group():
    api = _api()
    op = UserGroupOperation(_groups({
        "name": "Templar Users",
        "gui_access": "INTERNAL",
        "host_groups": [
            {"name": "Linux servers", "permission": "NONE"},
            {"name": "Virtual machines", "permission": "READ"},
        ],
        "template_groups": [
            {"name": "Test Template", "permission": "READ_WRITE"},
        ],
    }), api)
    op.execute()
    api.usergroup.create.assert_called_once_with(
        name="Templar Users",
        gui_access=1,
        hostgroup_rights=[
            {"id": "2", "permission": 0},
            {"id": "3", "permission": 2},
        ],
        templategroup_rights=[
            {"id": "10", "permission": 3},
        ],
    )


def test_updates_existing_user_group():
    api = _api(existing_ugroups=[{"usrgrpid": "99", "name": "Templar Users"}])
    op = UserGroupOperation(_groups({
        "name": "Templar Users",
        "gui_access": "DISABLED",
    }), api)
    op.execute()
    api.usergroup.update.assert_called_once_with(usrgrpid="99", gui_access=3)
    api.usergroup.create.assert_not_called()


def test_unknown_host_group_raises():
    api = _api()
    op = UserGroupOperation(_groups({
        "name": "Bad Group",
        "host_groups": [{"name": "Nonexistent", "permission": "READ"}],
    }), api)
    with pytest.raises(ValueError, match="Host group 'Nonexistent' not found"):
        op.execute()


def test_api_error_on_create_is_wrapped():
    api = _api()
    api.usergroup.create.side_effect = APIRequestError("network drop")
    op = UserGroupOperation(_groups({"name": "Ops Team", "gui_access": "DEFAULT"}), api)
    with pytest.raises(ExecutorApiError, match="Failed to create user group 'Ops Team'"):
        op.execute()


def test_api_error_on_update_is_wrapped():
    api = _api(existing_ugroups=[{"usrgrpid": "99", "name": "Ops Team"}])
    api.usergroup.update.side_effect = APIRequestError("network drop")
    op = UserGroupOperation(_groups({"name": "Ops Team", "gui_access": "DEFAULT"}), api)
    with pytest.raises(ExecutorApiError, match="Failed to update user group 'Ops Team'"):
        op.execute()
