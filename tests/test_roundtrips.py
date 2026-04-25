"""Round-trip tests: load decree YAML, decode via from_dict, re-serialize via to_dict, compare.

Each assertion runs the produced dict through yaml.safe_dump + yaml.safe_load before
comparing — that catches enum/custom-type leaks that == would silently accept (e.g. a
StrEnum member equals its value string but yaml.safe_dump rejects it).
"""
import copy
from pathlib import Path

import yaml

from zbxtemplar.decree import User, UserGroup
from zbxtemplar.decree.Action import Action
from zbxtemplar.decree.Encryption import HostEncryption
from zbxtemplar.decree.saml import SamlProvider


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_yaml(name):
    return yaml.safe_load((FIXTURES_DIR / name).read_text())


def _safe_roundtrip(data):
    return yaml.safe_load(yaml.safe_dump(data))


def test_user_roundtrip():
    data = _load_yaml("sample_set_user.yml")
    for user_dict in data["add_user"]:
        reference = copy.deepcopy(user_dict)
        user = User.from_dict(user_dict)
        assert _safe_roundtrip(user.to_dict()) == reference


def test_user_group_roundtrip():
    data = _load_yaml("sample_user_group.yml")
    for group_dict in data["user_group"]:
        reference = copy.deepcopy(group_dict)
        group = UserGroup.from_dict(group_dict)
        assert _safe_roundtrip(group.to_dict()) == reference


def test_saml_roundtrip():
    data = _load_yaml("sample_saml_config.yml")
    reference = copy.deepcopy(data["saml"])
    provider = SamlProvider.from_dict(data["saml"])
    assert _safe_roundtrip(provider.to_dict()) == reference


def test_host_encryption_roundtrip():
    data = _load_yaml("sample_encryption_decree.yml")
    for host_dict in data["encryption"]["hosts"]:
        reference = copy.deepcopy(host_dict)
        host = HostEncryption.from_dict(host_dict)
        assert _safe_roundtrip(host.to_dict()) == reference


def test_action_roundtrip():
    data = _load_yaml("sample_actions_decree.yml")
    for action_dict in data["actions"]:
        reference = copy.deepcopy(action_dict)
        action = Action.from_dict(action_dict)
        assert _safe_roundtrip(action.to_dict()) == reference