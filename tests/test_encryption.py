import pytest

from zbxtemplar.modules.DecreeModule import DecreeModule
from zbxtemplar.decree.Encryption import EncryptionMode, HostEncryption


class EmptyDecree(DecreeModule):
    def compose(self):
        pass


def test_check_requires_both_psk_fields():
    entry = HostEncryption.from_dict({
        "host": "host1",
        "connect": "PSK",
        "accept": "UNENCRYPTED",
        "psk": "mysecret"
    })
    with pytest.raises(ValueError, match="are required when PSK mode is enabled"):
        entry.check()

    entry = HostEncryption.from_dict({
        "host": "host1",
        "connect": "UNENCRYPTED",
        "accept": "PSK",
        "psk_identity": "myid"
    })
    with pytest.raises(ValueError, match="are required when PSK mode is enabled"):
        entry.check()


def test_from_dict():
    unenc = HostEncryption.from_dict({
        "host": "h1", "connect": "UNENCRYPTED", "accept": "UNENCRYPTED"})
    assert unenc.connect == [EncryptionMode.UNENCRYPTED]
    assert unenc.psk is None

    psk = HostEncryption.from_dict({
        "host": "h2", "connect": "PSK", "accept": "UNENCRYPTED, PSK",
        "psk_identity": "id1", "psk": "secret1"})
    assert psk.connect == [EncryptionMode.PSK]
    assert psk.accept == [EncryptionMode.UNENCRYPTED, EncryptionMode.PSK]
    assert psk.psk == "secret1"

    cert = HostEncryption.from_dict({
        "host": "h3", "connect": "CERT", "accept": "CERT",
        "issuer": "some_issuer", "subject": "some_subject"})
    assert cert.connect == [EncryptionMode.CERT]
    assert cert.issuer == "some_issuer"


def test_from_dict_ignores_stray_credentials():
    """PSK creds in dict but mode is UNENCRYPTED — silently ignored."""
    entry = HostEncryption.from_dict({
        "host": "host4",
        "connect": "UNENCRYPTED",
        "accept": "UNENCRYPTED",
        "psk": "stray",
        "psk_identity": "stray_id"
    })
    assert entry.psk is None
    assert entry.psk_identity is None


def test_programmatic_api():
    h = HostEncryption("myhost")
    h.set_psk(connect=True, accept=True, identity="id1", psk="secret1")
    h.set_cert(connect=False, accept=True, issuer="iss", subject="sub")
    h.check()

    assert h.connect == [EncryptionMode.PSK]
    assert h.accept == [EncryptionMode.PSK, EncryptionMode.CERT]
    assert h.psk == "secret1"
    assert h.issuer == "iss"


def test_to_dict_roundtrip():
    h = HostEncryption("app-01", accept_unencrypted=True)
    h.set_psk(connect=True, accept=True, identity="id1", psk="secret1")
    d = h.to_dict()

    assert d == {
        "host": "app-01",
        "connect": "PSK",
        "accept": "UNENCRYPTED, PSK",
        "psk_identity": "id1",
        "psk": "secret1",
    }

    restored = HostEncryption.from_dict(d)
    assert restored.host == h.host
    assert restored.connect == h.connect
    assert restored.accept == h.accept
    assert restored.psk == h.psk


def test_decree_module_export():
    module = EmptyDecree()
    defaults = module.set_encryption_defaults()
    defaults.set_cert(connect=True, accept=True, issuer="CN=Root CA")
    host_encryption = module.add_host_encryption("app-01")
    host_encryption.set_cert(connect=True, accept=True, subject="CN=app-01")

    export = module.to_export()
    assert "encryption" in export
    assert export["encryption"]["host_defaults"] == {
        "connect": "CERT",
        "accept": "CERT",
        "issuer": "CN=Root CA",
    }
    assert export["encryption"]["hosts"] == [{
        "host": "app-01",
        "connect": "CERT",
        "accept": "CERT",
        "subject": "CN=app-01",
    }]
