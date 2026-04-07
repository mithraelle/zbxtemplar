import pytest

from zbxtemplar.executor.Executor import _resolve_env, _preflight_env_check


# --- resolve_env ---

def test_resolve_plain_string():
    assert _resolve_env("hello") == "hello"


def test_resolve_env_var(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "secret")
    assert _resolve_env("${TEST_VAR}") == "secret"


def test_resolve_env_var_embedded(monkeypatch):
    monkeypatch.setenv("HOST", "db.local")
    assert _resolve_env("jdbc://${HOST}:5432") == "jdbc://db.local:5432"


def test_resolve_env_missing():
    with pytest.raises(ValueError, match="NONEXISTENT"):
        _resolve_env("${NONEXISTENT}")


def test_resolve_non_string():
    assert _resolve_env(42) == 42


# --- preflight ---

def test_preflight_passes(monkeypatch):
    monkeypatch.setenv("A", "1")
    _preflight_env_check({"key": "${A}"})  # no exception


def test_preflight_reports_all_missing():
    with pytest.raises(ValueError, match="MISSING_A") as exc:
        _preflight_env_check({"x": "${MISSING_A}", "y": [{"z": "${MISSING_B}"}]})
    assert "MISSING_B" in str(exc.value)