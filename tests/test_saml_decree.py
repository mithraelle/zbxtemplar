import pytest

from zbxtemplar.decree import (
    ActiveStatus,
    ProvisionStatus,
    SamlProvider,
    SamlProvisionGroup,
    SamlProvisionMedia,
    ScimStatus,
    Severity,
    UserGroup,
)
from zbxtemplar.catalog.zabbix_7_4 import MediaType, UserRole
from zbxtemplar.dicts.Decree import Decree
from zbxtemplar.modules.DecreeModule import DecreeModule
from zbxtemplar.zabbix import YesNo


class EmptyDecree(DecreeModule):
    def compose(self):
        pass


def _sample_saml_dict():
    return {
        "provision_status": "ENABLED",
        "scim_status": "DISABLED",
        "idp_entityid": "http://www.okta.com/example",
        "sso_url": "https://example.okta.com/sso/saml",
        "username_attribute": "usrEmail",
        "sp_entityid": "zabbix",
        "user_username": "firstName",
        "user_lastname": "lastName",
        "nameid_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        "sign_messages": "NO",
        "sign_assertions": "YES",
        "sign_authn_requests": "NO",
        "sign_logout_requests": "NO",
        "sign_logout_responses": "NO",
        "encrypt_nameid": "NO",
        "encrypt_assertions": "YES",
        "saml_case_sensitive": "YES",
        "group_name": "groups",
        "disabled_user_group": "Disabled",
        "provision_groups": [
            {
                "name": "zabbix-admins",
                "role": UserRole.SUPER_ADMIN,
                "user_groups": ["Operations"],
            },
        ],
        "provision_media": [
            {
                "name": "Email from Okta",
                "type": MediaType.EMAIL,
                "attribute": "email",
                "active": "ENABLED",
                "severity": [
                    Severity.AVERAGE,
                    Severity.HIGH,
                    Severity.DISASTER,
                ],
                "period": "1-7,00:00-24:00",
            },
        ],
    }


def test_saml_provider_from_dict_uses_schema_deserialization():
    provider = SamlProvider.from_dict(_sample_saml_dict())

    assert provider.provision_status == ProvisionStatus.ENABLED
    assert provider.scim_status == ScimStatus.DISABLED
    assert provider.user_username == "firstName"
    assert provider.user_lastname == "lastName"
    assert provider.sign_messages == YesNo.NO
    assert provider.sign_assertions == YesNo.YES
    assert provider.provision_groups[0].name == "zabbix-admins"
    assert provider.provision_groups[0].role == UserRole.SUPER_ADMIN
    assert provider.provision_groups[0].user_groups[0].name == "Operations"
    assert provider.provision_media[0].type == MediaType.EMAIL
    assert provider.provision_media[0].attribute == "email"
    assert provider.provision_media[0].active == ActiveStatus.ENABLED
    assert provider.provision_media[0].severity == [
        Severity.AVERAGE,
        Severity.HIGH,
        Severity.DISASTER,
    ]

    assert provider.to_dict()["provision_status"] == 1
    assert provider.to_dict()["scim_status"] == 0
    assert provider.to_dict()["sign_messages"] == "NO"
    assert provider.to_dict()["sign_assertions"] == "YES"
    assert provider.to_dict()["provision_media"][0] == {
        "type": "Email",
        "attribute": "email",
        "severity": "AVERAGE,HIGH,DISASTER",
        "period": "1-7,00:00-24:00",
        "name": "Email from Okta",
        "active": 0,
    }


def test_saml_provider_defaults_saml_and_scim_disabled():
    provider = SamlProvider.from_dict({
        "idp_entityid": "http://www.okta.com/example",
        "sso_url": "https://example.okta.com/sso/saml",
        "username_attribute": "usrEmail",
        "sp_entityid": "zabbix",
    })

    assert provider.provision_status is None
    assert provider.scim_status is None
    assert provider.provision_groups is None
    assert provider.provision_media is None


def test_saml_provision_media_defaults():
    provider = SamlProvider.from_dict({
        "idp_entityid": "http://www.okta.com/example",
        "sso_url": "https://example.okta.com/sso/saml",
        "username_attribute": "usrEmail",
        "sp_entityid": "zabbix",
        "provision_status": "ENABLED",
        "group_name": "groups",
        "disabled_user_group": "Disabled",
        "provision_groups": [{
            "name": "zabbix-admins",
            "role": UserRole.SUPER_ADMIN,
            "user_groups": ["Operations"],
        }],
        "provision_media": [{
            "name": "Email from Okta",
            "type": MediaType.EMAIL,
            "attribute": "email",
        }],
    })

    media = provider.provision_media[0]

    assert media.active is None
    assert media.severity is None
    assert media.period is None


def test_saml_provider_requires_create_fields():
    with pytest.raises(ValueError, match="missing required key.*idp_entityid"):
        SamlProvider.from_dict({
            "sso_url": "https://example.okta.com/sso/saml",
            "username_attribute": "usrEmail",
            "sp_entityid": "zabbix",
        })


def test_saml_provider_requires_provisioning_fields_when_enabled():
    with pytest.raises(ValueError, match="group_name: required"):
        SamlProvider.from_dict({
            "provision_status": "ENABLED",
            "idp_entityid": "http://www.okta.com/example",
            "sso_url": "https://example.okta.com/sso/saml",
            "username_attribute": "usrEmail",
            "sp_entityid": "zabbix",
        })

    with pytest.raises(ValueError, match="disabled_user_group: required"):
        SamlProvider.from_dict({
            "provision_status": "ENABLED",
            "idp_entityid": "http://www.okta.com/example",
            "sso_url": "https://example.okta.com/sso/saml",
            "username_attribute": "usrEmail",
            "sp_entityid": "zabbix",
            "group_name": "groups",
        })

    with pytest.raises(ValueError, match="provision_groups: required"):
        SamlProvider.from_dict({
            "provision_status": "ENABLED",
            "idp_entityid": "http://www.okta.com/example",
            "sso_url": "https://example.okta.com/sso/saml",
            "username_attribute": "usrEmail",
            "sp_entityid": "zabbix",
            "group_name": "groups",
            "disabled_user_group": "Disabled",
        })


def test_decree_accepts_saml_top_level_key():
    decree = Decree.from_dict({"saml": _sample_saml_dict()})

    assert decree.saml.provision_groups[0].user_groups[0].name == "Operations"
    assert decree.saml.to_dict()["provision_groups"][0]["user_groups"] == ["Operations"]


def test_decree_module_exports_saml_after_user_groups():
    module = EmptyDecree()
    ops = module.add_user_group("Operations")
    disabled = module.add_user_group("Disabled")
    provider = module.set_saml(
        idp_entityid="http://www.okta.com/example",
        sp_entityid="zabbix",
        sso_url="https://example.okta.com/sso/saml",
        username_attribute="usrEmail",
    )
    provider.set_provisioning(
        group_name="groups",
        disabled_user_group=disabled,
        groups=SamlProvisionGroup("zabbix-admins", UserRole.SUPER_ADMIN, [ops]),
    )

    export = module.to_export()

    assert list(export) == ["user_group", "saml"]
    assert export["saml"] == {
        "provision_status": 1,
        "scim_status": 0,
        "idp_entityid": "http://www.okta.com/example",
        "sso_url": "https://example.okta.com/sso/saml",
        "username_attribute": "usrEmail",
        "sp_entityid": "zabbix",
        "group_name": "groups",
        "disabled_user_group": "Disabled",
        "sign_assertions": "NO",
        "sign_authn_requests": "NO",
        "sign_messages": "NO",
        "sign_logout_requests": "NO",
        "sign_logout_responses": "NO",
        "encrypt_assertions": "NO",
        "encrypt_nameid": "NO",
        "saml_case_sensitive": "YES",
        "provision_groups": [{
            "name": "zabbix-admins",
            "role": "Super admin role",
            "user_groups": ["Operations"],
        }],
    }


def test_saml_provider_rejects_orphan_provision_mappings():
    provider = SamlProvider(
        idp_entityid="http://www.okta.com/example",
        sp_entityid="zabbix",
        sso_url="https://example.okta.com/sso/saml",
        username_attribute="usrEmail",
    )
    provider.add_provision_group(
        SamlProvisionGroup("zabbix-admins", UserRole.SUPER_ADMIN, ["Operations"])
    )

    with pytest.raises(ValueError, match="provisioning is disabled"):
        provider.to_dict()


def test_saml_provider_fluent_setters():
    provider = SamlProvider(
        idp_entityid="http://www.okta.com/example",
        sp_entityid="zabbix",
        sso_url="https://example.okta.com/sso/saml",
        username_attribute="usrEmail",
    )
    provider.set_nameid(
        "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
        encrypt=True,
    )
    provider.set_security(sign_assertions=True, encrypt_assertions=True)
    provider.set_case_sensitive(False)
    provider.set_provisioning(
        group_name="groups",
        disabled_user_group=UserGroup("Disabled"),
        user_username="firstName",
        groups=SamlProvisionGroup("zabbix-admins", UserRole.SUPER_ADMIN, ["Operations"]),
        media=SamlProvisionMedia("Email", MediaType.EMAIL, "email"),
    )

    exported = provider.to_dict()

    assert exported["nameid_format"] == "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
    assert exported["encrypt_nameid"] == "YES"
    assert exported["sign_assertions"] == "YES"
    assert exported["sign_messages"] == "NO"
    assert exported["encrypt_assertions"] == "YES"
    assert exported["provision_status"] == 1
    assert exported["group_name"] == "groups"
    assert exported["disabled_user_group"] == "Disabled"
    assert exported["saml_case_sensitive"] == "NO"
    assert exported["user_username"] == "firstName"
    assert exported["provision_groups"][0]["name"] == "zabbix-admins"
    assert exported["provision_media"][0]["name"] == "Email"


def test_saml_provider_rejects_duplicate_provision_entries():
    provider = SamlProvider(
        idp_entityid="http://www.okta.com/example",
        sp_entityid="zabbix",
        sso_url="https://example.okta.com/sso/saml",
        username_attribute="usrEmail",
    )
    group = SamlProvisionGroup("zabbix-admins", UserRole.SUPER_ADMIN, ["Operations"])
    media = SamlProvisionMedia("Email", MediaType.EMAIL, "email")
    provider.add_provision_group(group)
    provider.add_provision_media(media)

    with pytest.raises(ValueError, match="Duplicate provision_group 'zabbix-admins'"):
        provider.add_provision_group(
            SamlProvisionGroup("zabbix-admins", UserRole.ADMIN, ["Operations"])
        )
    with pytest.raises(ValueError, match="Duplicate provision_media 'Email'"):
        provider.add_provision_media(SamlProvisionMedia("Email", MediaType.EMAIL, "other"))


def test_add_saml_rejects_second_provider():
    module = EmptyDecree()
    module.set_saml(
        idp_entityid="http://www.okta.com/example",
        sp_entityid="zabbix",
        sso_url="https://example.okta.com/sso/saml",
        username_attribute="usrEmail",
    )

    with pytest.raises(ValueError, match="SAML provider already configured"):
        module.set_saml(
            idp_entityid="http://www.okta.com/example",
            sp_entityid="zabbix",
            sso_url="https://example.okta.com/sso/saml",
            username_attribute="usrEmail",
        )
