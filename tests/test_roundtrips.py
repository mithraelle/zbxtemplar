"""Round-trip tests: load decree YAML, decode via from_dict, re-serialize via to_dict, compare."""
from pathlib import Path

import yaml

from zbxtemplar.decree import User, UserGroup
from zbxtemplar.decree.Action import Action
from zbxtemplar.decree.Encryption import HostEncryption
from zbxtemplar.decree.saml import SamlProvider


EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def _load_yaml(name):
    return yaml.safe_load((EXAMPLES_DIR / name).read_text())


def test_user_roundtrip():
    data = _load_yaml("sample_set_user.yml")
    for user_dict in data["add_user"]:
        user = User.from_dict(user_dict)
        assert user.to_dict() == user_dict


def test_user_group_roundtrip():
    data = _load_yaml("sample_user_group.yml")
    for group_dict in data["user_group"]:
        group = UserGroup.from_dict(group_dict)
        assert group.to_dict() == group_dict


def test_saml_roundtrip():
    data = _load_yaml("sample_saml_config.yml")
    provider = SamlProvider.from_dict(data["saml"])
    assert provider.to_dict() == data["saml"]


def test_host_encryption_roundtrip():
    data = _load_yaml("sample_encryption_decree.yml")
    for host_dict in data["encryption"]["hosts"]:
        host = HostEncryption.from_dict(host_dict)
        assert host.to_dict() == host_dict


def test_action_roundtrip():
    data = _load_yaml("sample_actions_decree.yml")
    for action_dict in data["actions"]:
        action = Action.from_dict(action_dict)
        assert action.to_dict() == action_dict