from unittest.mock import MagicMock

import pytest

from zbxtemplar.decree.Encryption import Encryption, HostEncryption, EncryptionMode
from zbxtemplar.executor.EncryptionExecutor import EncryptionExecutor
from zbxtemplar.executor.Executor import Executor


@pytest.fixture
def api_mock():
    return MagicMock()


def test_encryption_executor_missing_host(api_mock):
    api_mock.host.get.return_value = []
    executor = EncryptionExecutor(api_mock)
    entry = HostEncryption("host1", connect_unencrypted=True, accept_unencrypted=True)

    with pytest.raises(ValueError, match="Host 'host1' not found"):
        executor._apply([entry])


def test_encryption_executor_update_psk(api_mock):
    api_mock.host.get.return_value = [{
        "hostid": "1001",
        "host": "host1",
        "tls_connect": "1",
        "tls_accept": "1",
        "tls_issuer": "",
        "tls_subject": "",
        "tls_psk_identity": ""
    }]
    executor = EncryptionExecutor(api_mock)

    entry = HostEncryption("host1", accept_unencrypted=True)
    entry.set_psk(connect=True, accept=True, identity="myid", psk="mypsk")

    executor._apply([entry])

    api_mock.host.update.assert_called_once_with(
        hostid="1001",
        tls_connect=2,
        tls_accept=3,  # 1 (UNENCRYPTED) | 2 (PSK)
        tls_psk_identity="myid",
        tls_psk="mypsk"
    )


def test_encryption_executor_no_update_needed(api_mock):
    api_mock.host.get.return_value = [{
        "hostid": "1002",
        "host": "host2",
        "tls_connect": "1",
        "tls_accept": "1",
        "tls_issuer": "",
        "tls_subject": "",
        "tls_psk_identity": ""
    }]
    executor = EncryptionExecutor(api_mock)

    entry = HostEncryption("host2", connect_unencrypted=True, accept_unencrypted=True)

    executor._apply([entry])
    api_mock.host.update.assert_not_called()


def test_decree_merges_defaults(api_mock):
    api_mock.host.get.return_value = [{
        "hostid": "1003",
        "host": "defaulted_host",
        "tls_connect": "1",
        "tls_accept": "1",
        "tls_issuer": "",
        "tls_subject": "",
        "tls_psk_identity": ""
    }]
    ex = Executor(api_mock)

    ex.decree({"encryption": {
        "host_defaults": {"connect": "UNENCRYPTED", "accept": "UNENCRYPTED"},
        "hosts": [{"host": "defaulted_host"}]
    }})

    api_mock.host.get.assert_called_once()
    api_mock.host.update.assert_not_called()


def test_decree_psk_in_defaults(api_mock):
    api_mock.host.get.return_value = [{
        "hostid": "1004",
        "host": "psk_host",
        "tls_connect": "1",
        "tls_accept": "1",
        "tls_issuer": "",
        "tls_subject": "",
        "tls_psk_identity": ""
    }]
    ex = Executor(api_mock)

    ex.decree({"encryption": {
        "host_defaults": {
            "connect": "PSK", "accept": "PSK",
            "psk_identity": "root_id", "psk": "root_secret"
        },
        "hosts": [{"host": "psk_host"}]
    }})

    api_mock.host.update.assert_called_once_with(
        hostid="1004", tls_connect=2, tls_accept=2,
        tls_psk_identity="root_id", tls_psk="root_secret"
    )


def test_decree_host_overrides_psk_defaults_to_cert(api_mock):
    api_mock.host.get.return_value = [{
        "hostid": "1005",
        "host": "cert_host",
        "tls_connect": "1",
        "tls_accept": "1",
        "tls_issuer": "",
        "tls_subject": "",
        "tls_psk_identity": ""
    }]
    ex = Executor(api_mock)

    ex.decree({"encryption": {
        "host_defaults": {
            "connect": "PSK", "accept": "UNENCRYPTED, PSK",
            "psk_identity": "default_id", "psk": "default_secret"
        },
        "hosts": [{
            "host": "cert_host",
            "connect": "CERT", "accept": "UNENCRYPTED, CERT",
            "issuer": "my_issuer", "subject": "my_subject"
        }]
    }})

    api_mock.host.update.assert_called_once_with(
        hostid="1005", tls_connect=4,
        tls_accept=5,  # 1 | 4
        tls_issuer="my_issuer", tls_subject="my_subject"
    )


def test_decree_host_overrides_cert_defaults_to_psk(api_mock):
    api_mock.host.get.return_value = [{
        "hostid": "1006",
        "host": "psk_only",
        "tls_connect": "1",
        "tls_accept": "1",
        "tls_issuer": "",
        "tls_subject": "",
        "tls_psk_identity": ""
    }]
    ex = Executor(api_mock)

    ex.decree({"encryption": {
        "host_defaults": {
            "connect": "CERT", "accept": "CERT",
            "issuer": "default_issuer", "subject": "default_subject"
        },
        "hosts": [{
            "host": "psk_only",
            "connect": "PSK", "accept": "PSK",
            "psk_identity": "my_id", "psk": "my_secret"
        }]
    }})

    api_mock.host.update.assert_called_once_with(
        hostid="1006", tls_connect=2, tls_accept=2,
        tls_psk_identity="my_id", tls_psk="my_secret"
    )


def test_decree_host_inherits_defaults(api_mock):
    api_mock.host.get.return_value = [{
        "hostid": "1007",
        "host": "inheriting_host",
        "tls_connect": "1",
        "tls_accept": "1",
        "tls_issuer": "",
        "tls_subject": "",
        "tls_psk_identity": ""
    }]
    ex = Executor(api_mock)

    ex.decree({"encryption": {
        "host_defaults": {
            "connect": "PSK", "accept": "UNENCRYPTED, PSK",
            "psk_identity": "shared_id", "psk": "shared_secret"
        },
        "hosts": [{"host": "inheriting_host"}]
    }})

    api_mock.host.update.assert_called_once_with(
        hostid="1007", tls_connect=2,
        tls_accept=3,  # 1 | 2
        tls_psk_identity="shared_id", tls_psk="shared_secret"
    )


def test_decree_requires_host():
    ex = Executor(MagicMock())

    with pytest.raises(ValueError, match="requires 'host' field"):
        ex.decree({"encryption": {
            "host_defaults": {"connect": "UNENCRYPTED", "accept": "UNENCRYPTED"},
            "hosts": [{"connect": "UNENCRYPTED"}]
        }})