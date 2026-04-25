import time

import pytest
import yaml

from zbxtemplar.decree.Token import Token


# --- Normalization (the non-obvious coercions) ---

def test_normalization_sentinels():
    t = Token("t", store_at="STDOUT", expires_at="NEVER")
    assert t.store_at == Token.STDOUT
    assert t.expires_at == Token.EXPIRES_NEVER

    store_at = ".secrets/api.token"
    future = int(time.time()) + 3600
    t = Token("t", store_at=store_at, expires_at=str(future))
    assert t.expires_at == future
    assert t.store_at == store_at

# --- Rejection ---

def test_bad_name_rejected():
    with pytest.raises(ValueError, match="token.name"):
        Token("", store_at="STDOUT")


def test_bad_store_at_rejected():
    with pytest.raises(ValueError, match="token.store_at"):
        Token("t", store_at="")


def test_bool_expires_at_rejected():
    """bool is a subclass of int in Python — must not slip through."""
    with pytest.raises(ValueError, match="token.expires_at"):
        Token("t", store_at="STDOUT", expires_at=True)


def test_garbage_expires_at_rejected():
    with pytest.raises(ValueError, match="token.expires_at"):
        Token("t", store_at="STDOUT", expires_at="banana")


def test_past_expires_at_accepted_at_construction():
    """Past-timestamp check is deferred to executor time via assert_expires_in_future()."""
    t = Token("t", store_at="STDOUT", expires_at=1000000000)
    assert t.expires_at == 1000000000
    with pytest.raises(ValueError, match="in the past"):
        t.assert_expires_in_future()


# --- from_dict ---

def test_from_dict():
    t = Token.from_dict({"name": "api-reader", "store_at": "STDOUT", "expires_at": "NEVER"})
    assert t.name == "api-reader"
    assert t.store_at == Token.STDOUT
    assert t.expires_at == Token.EXPIRES_NEVER

    with pytest.raises(ValueError, match="missing required key.*store_at"):
        Token.from_dict({"name": "t"})

# --- to_dict ---

def test_to_dict_serializes_sentinels():
    t = Token("t", store_at="STDOUT", expires_at="NEVER")
    d = t.to_dict()
    assert d["store_at"] == "STDOUT"
    assert d["expires_at"] == "NEVER"

# --- Round-trip ---

def test_round_trip():
    original = Token("api-reader", store_at="STDOUT", expires_at="NEVER")
    reference = yaml.safe_load(yaml.safe_dump(original.to_dict()))
    restored = Token.from_dict(reference)
    assert yaml.safe_load(yaml.safe_dump(restored.to_dict())) == reference
