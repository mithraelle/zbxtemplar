from unittest.mock import MagicMock

import pytest

from zbxtemplar.dicts.Decree import Decree
from zbxtemplar.executor.DecreeExecutor import DecreeExecutor


def _api_with_lookups():
    api = MagicMock()
    api.role.get.return_value = [
        {"roleid": "3", "name": "Super admin role"},
    ]
    api.usergroup.get.return_value = [
        {"usrgrpid": "7", "name": "Operations"},
        {"usrgrpid": "8", "name": "Disabled"},
    ]
    api.mediatype.get.return_value = [
        {"mediatypeid": "1", "name": "Email"},
    ]
    api.hostgroup.get.return_value = []
    api.templategroup.get.return_value = []
    return api


def _decree(provider):
    return Decree.from_dict({"saml": provider})


def _minimal_provider():
    return {
        "idp_entityid": "http://idp.example",
        "sp_entityid": "zabbix",
        "sso_url": "https://idp.example/sso",
        "username_attribute": "uid",
    }


def _full_provider():
    return {
        "idp_entityid": "http://www.okta.com/example",
        "sp_entityid": "zabbix",
        "sso_url": "https://example.okta.com/sso/saml",
        "username_attribute": "usrEmail",
        "sign_assertions": "YES",
        "encrypt_assertions": "YES",
        "saml_case_sensitive": "NO",
        "provision_status": "ENABLED",
        "scim_status": "DISABLED",
        "group_name": "groups",
        "disabled_user_group": "Disabled",
        "user_username": "firstName",
        "provision_groups": [{
            "name": "zabbix-admins",
            "role": "Super admin role",
            "user_groups": ["Operations"],
        }],
        "provision_media": [{
            "name": "Email",
            "type": "Email",
            "attribute": "email",
        }],
    }


def test_saml_creates_when_no_userdirectory_exists():
    api = _api_with_lookups()
    api.userdirectory.get.return_value = []
    api.userdirectory.create.return_value = {"userdirectoryids": ["42"]}

    DecreeExecutor(_decree(_full_provider()), api).execute(only_action="saml")

    api.userdirectory.create.assert_called_once()
    params = api.userdirectory.create.call_args.kwargs
    assert params["idp_type"] == 2
    assert params["name"] == "SAML"
    assert params["idp_entityid"] == "http://www.okta.com/example"
    assert params["sign_assertions"] == 1
    assert params["encrypt_assertions"] == 1
    assert params["provision_status"] == 1
    assert params["scim_status"] == 0
    assert params["provision_groups"] == [{
        "name": "zabbix-admins",
        "roleid": "3",
        "user_groups": [{"usrgrpid": "7"}],
    }]
    assert params["provision_media"] == [{
        "name": "Email",
        "mediatypeid": "1",
        "attribute": "email",
    }]
    api.userdirectory.update.assert_not_called()
    api.authentication.update.assert_called_once_with(
        saml_auth_enabled=1,
        saml_jit_status=1,
        disabled_usrgrpid="8",
        saml_case_sensitive=0,
    )


def test_saml_updates_existing_userdirectory():
    api = _api_with_lookups()
    api.userdirectory.get.return_value = [{"userdirectoryid": "9"}]

    DecreeExecutor(_decree(_minimal_provider()), api).execute(only_action="saml")

    api.userdirectory.update.assert_called_once()
    params = api.userdirectory.update.call_args.kwargs
    assert params["userdirectoryid"] == "9"
    assert "idp_type" not in params
    assert params["idp_entityid"] == "http://idp.example"
    api.userdirectory.create.assert_not_called()
    api.authentication.update.assert_called_once_with(
        saml_auth_enabled=1, saml_jit_status=0, saml_case_sensitive=1
    )


def test_saml_rejects_unknown_role():
    api = _api_with_lookups()
    api.role.get.return_value = []
    api.userdirectory.get.return_value = []

    with pytest.raises(ValueError, match="Role 'Super admin role' not found"):
        DecreeExecutor(_decree(_full_provider()), api).execute(only_action="saml")


def test_saml_rejects_unknown_user_group():
    api = _api_with_lookups()
    api.usergroup.get.return_value = []
    api.userdirectory.get.return_value = []

    with pytest.raises(ValueError, match="User group 'Operations' not found"):
        DecreeExecutor(_decree(_full_provider()), api).execute(only_action="saml")


def test_saml_rejects_unknown_media_type():
    api = _api_with_lookups()
    api.mediatype.get.return_value = []
    api.userdirectory.get.return_value = []

    with pytest.raises(ValueError, match="Media type 'Email' not found"):
        DecreeExecutor(_decree(_full_provider()), api).execute(only_action="saml")