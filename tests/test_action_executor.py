from unittest.mock import MagicMock

import pytest

from zbxtemplar.executor.ActionExecutor import ActionExecutor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zabbix_utils import APIRequestError


def _api(existing_actions=None):
    api = MagicMock()
    api.usergroup.get.return_value = [{"usrgrpid": "7", "name": "Ops Team"}]
    api.user.get.return_value = [{"userid": "10", "username": "alice"}]
    api.mediatype.get.return_value = [{"mediatypeid": "5", "name": "Email"}]
    api.hostgroup.get.return_value = [{"groupid": "2", "name": "Linux servers"}]
    api.template.get.return_value = [{"templateid": "100", "name": "Linux by Zabbix agent"}]
    api.action.get.return_value = (
        [{"actionid": a["actionid"], "name": a["name"]} for a in existing_actions]
        if existing_actions else []
    )
    return api


def _simple_action(name="Notify Ops"):
    return {
        "name": name,
        "eventsource": 0,
        "operations": [],
    }


def test_creates_action():
    api = _api()
    ActionExecutor(api).execute([_simple_action()])
    api.action.create.assert_called_once()
    assert api.action.create.call_args[1]["name"] == "Notify Ops"


def test_updates_existing_action():
    api = _api(existing_actions=[{"actionid": "42", "name": "Notify Ops"}])
    ActionExecutor(api).execute([_simple_action()])
    api.action.update.assert_called_once()
    call = api.action.update.call_args[1]
    assert call["actionid"] == "42"
    assert "name" not in call
    api.action.create.assert_not_called()


def test_resolves_hostgroup_condition():
    api = _api()
    api.hostgroup.get.return_value = [{"groupid": "2", "name": "Linux servers"}]
    action = {
        "name": "Test",
        "eventsource": 0,
        "filter": {
            "evaltype": 0,
            "conditions": [{"conditiontype": 0, "operator": 0, "value": "Linux servers"}],
        },
        "operations": [],
    }
    ActionExecutor(api).execute([action])
    assert action["filter"]["conditions"][0]["value"] == "2"


def test_unknown_condition_entity_raises():
    api = _api()
    action = {
        "name": "Test",
        "eventsource": 0,
        "filter": {
            "evaltype": 0,
            "conditions": [{"conditiontype": 0, "operator": 0, "value": "Nonexistent group"}],
        },
        "operations": [],
    }
    with pytest.raises(ValueError, match="Host group 'Nonexistent group' not found"):
        ActionExecutor(api).execute([action])


def test_resolves_opmessage_grp():
    api = _api()
    action = {
        "name": "Test",
        "eventsource": 0,
        "operations": [{
            "operationtype": 0,
            "opmessage": {"default_msg": 1},
            "opmessage_grp": [{"usrgrpid": "Ops Team"}],
        }],
    }
    ActionExecutor(api).execute([action])
    assert action["operations"][0]["opmessage_grp"][0]["usrgrpid"] == "7"


def test_resolves_opmessage_usr():
    api = _api()
    action = {
        "name": "Test",
        "eventsource": 0,
        "operations": [{
            "operationtype": 0,
            "opmessage": {"default_msg": 1},
            "opmessage_usr": [{"userid": "alice"}],
        }],
    }
    ActionExecutor(api).execute([action])
    assert action["operations"][0]["opmessage_usr"][0]["userid"] == "10"


def test_resolves_opmessage_media_type():
    api = _api()
    action = {
        "name": "Test",
        "eventsource": 0,
        "operations": [{
            "operationtype": 0,
            "opmessage": {"default_msg": 1, "mediatypeid": "Email"},
        }],
    }
    ActionExecutor(api).execute([action])
    assert action["operations"][0]["opmessage"]["mediatypeid"] == "5"


def test_unknown_operation_user_group_raises():
    api = _api()
    action = {
        "name": "Test",
        "eventsource": 0,
        "operations": [{"operationtype": 0, "opmessage_grp": [{"usrgrpid": "Nobody"}]}],
    }
    with pytest.raises(ValueError, match="User group 'Nobody' not found"):
        ActionExecutor(api).execute([action])


def test_api_error_on_create_is_wrapped():
    api = _api()
    api.action.create.side_effect = APIRequestError("network drop")
    with pytest.raises(ExecutorApiError, match="Failed to create action 'Notify Ops'"):
        ActionExecutor(api).execute([_simple_action()])


def test_api_error_on_update_is_wrapped():
    api = _api(existing_actions=[{"actionid": "42", "name": "Notify Ops"}])
    api.action.update.side_effect = APIRequestError("network drop")
    with pytest.raises(ExecutorApiError, match="Failed to update action 'Notify Ops'"):
        ActionExecutor(api).execute([_simple_action()])