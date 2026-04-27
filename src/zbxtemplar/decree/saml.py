from typing import Self

from zbxtemplar.decree.DecreeEntity import DecreeEntity
from zbxtemplar.decree.UserGroup import UserGroup
from zbxtemplar.decree.User import UserMedia
from zbxtemplar.dicts.Schema import ApiStrEnum, SchemaField, SubsetBy
from zbxtemplar.zabbix.ZbxEntity import YesNo


class ProvisionStatus(ApiStrEnum):
    """Zabbix SAML provisioning status values."""
    DISABLED = "DISABLED", 0
    ENABLED  = "ENABLED",  1


class ScimStatus(ApiStrEnum):
    """Zabbix SCIM provisioning status values."""
    DISABLED = "DISABLED", 0
    ENABLED  = "ENABLED",  1


class SamlProvisionGroup(DecreeEntity):
    """SAML JIT provisioning group mapping managed by decree YAML."""

    _SCHEMA = [
        SchemaField("name", optional=False, description="SAML group attribute value to match."),
        SchemaField("role", optional=False, description="Zabbix role name to resolve via role.get."),
        SchemaField("user_groups", str_type="list[UserGroup]",
                    description="Zabbix user groups to attach to provisioned users.",
                    type=list[str], init=[]),
    ]

    def __init__(self, name: str, role: str, user_groups: list[UserGroup] | None = None):
        super()._wire_up(name=name, role=role)
        for group in user_groups or []:
            self.link_user_group(group)
        self._check()

    def link_user_group(self, group: UserGroup):
        if group.name in self.user_groups:
            raise ValueError(
                f"Duplicate user_group '{group.name}' on SAML provision group '{self.name}'"
            )
        self.user_groups.append(group.name)
        return self

    def _check(self) -> None:
        if not self.role:
            raise ValueError(
                f"SamlProvisionGroup '{self.name}': role must not be empty"
            )
        if not self.user_groups:
            raise ValueError(
                f"SamlProvisionGroup '{self.name}': user_groups must contain at least one group"
            )


class SamlProvisionMedia(UserMedia):
    """SAML JIT provisioning media mapping managed by decree YAML."""

    _SCHEMA = [
        SchemaField("name", optional=False, type=str, description="SAML provision media mapping name."),
        SchemaField("attribute", optional=False, type=str,
                    description="SAML attribute to copy into sendto at provisioning time."),
        *[f for f in UserMedia._SCHEMA if f.key != "sendto"],
    ]

    def __init__(self, name: str, media_type: str, attribute: str):
        super()._wire_up(name=name, type=media_type, attribute=attribute)


class SamlProvider(DecreeEntity):
    """Zabbix SAML userdirectory entry managed by decree YAML."""

    _SCHEMA = [
        SchemaField("idp_entityid", optional=False, description="Identity provider entity ID."),
        SchemaField("sp_entityid", optional=False, description="Zabbix service provider entity ID."),
        SchemaField("sso_url", optional=False, description="Identity provider SSO URL."),
        SchemaField("slo_url", description="Identity provider SLO URL.", api_default=""),
        SchemaField("username_attribute", optional=False,
                    description="SAML attribute to use as the Zabbix username."),


        SchemaField("nameid_format", description="SAML NameID format URI.", api_default=""),
        SchemaField("encrypt_nameid", str_type="YES or NO", description="Encrypt SAML NameID flag.",
                    type=YesNo, init=YesNo.NO),


        SchemaField("encrypt_assertions", str_type="YES or NO",
                    description="Encrypt SAML assertions flag.",
                    type=YesNo, init=YesNo.NO),
        SchemaField("sign_messages", str_type="YES or NO", description="Sign SAML messages flag.",
                    type=YesNo, init=YesNo.NO),
        SchemaField("sign_assertions", str_type="YES or NO", description="Sign SAML assertions flag.",
                    type=YesNo, init=YesNo.NO),
        SchemaField("sign_authn_requests", str_type="YES or NO",
                    description="Sign SAML authn requests flag.",
                    type=YesNo, init=YesNo.NO),
        SchemaField("sign_logout_requests", str_type="YES or NO",
                    description="Sign SAML logout requests flag.",
                    type=YesNo, init=YesNo.NO),
        SchemaField("sign_logout_responses", str_type="YES or NO",
                    description="Sign SAML logout responses flag.",
                    type=YesNo, init=YesNo.NO),


        SchemaField("provision_status", str_type="ProvisionStatus",
                    description="JIT provisioning status: DISABLED or ENABLED.",
                    type=ProvisionStatus, init=ProvisionStatus.DISABLED),
        SchemaField("group_name", description="SAML attribute carrying group membership.", init=None),
        SchemaField("user_username", description="SAML attribute to use as the user's first name.", init=None),
        SchemaField("user_lastname", description="SAML attribute to use as the user's last name.", init=None),
        SchemaField("disabled_user_group", str_type="UserGroup",
                    description="Zabbix user group to place deprovisioned SAML users into. For a real lockout, configure this group with users_status=DISABLED (gui_access=DISABLED alone blocks frontend login but not API token access).",
                    type=str, init=None),
        SchemaField("provision_groups", str_type="list[SamlProvisionGroup]",
                    description="SAML group to Zabbix role/user group mappings.",
                    type=list[SamlProvisionGroup], init=[], policy=SubsetBy("name")),
        SchemaField("provision_media", str_type="list[SamlProvisionMedia]",
                    description="SAML attribute to Zabbix media mappings.",
                    type=list[SamlProvisionMedia], init=[], policy=SubsetBy("name")),


        SchemaField("scim_status", str_type="ScimStatus",
                    description="SCIM provisioning status: DISABLED or ENABLED.",
                    type=ScimStatus, init=ScimStatus.DISABLED),


        SchemaField("saml_case_sensitive", str_type="YES or NO",
                    description="SAML case-sensitive login flag applied via authentication.update.",
                    type=YesNo, init=YesNo.YES),
    ]

    def __init__(
        self,
        idp_entityid: str,
        sp_entityid: str,
        sso_url: str,
        username_attribute: str,
        slo_url: str | None = None,
    ):
        super()._wire_up(
            idp_entityid=idp_entityid,
            sp_entityid=sp_entityid,
            sso_url=sso_url,
            username_attribute=username_attribute,
            slo_url=slo_url,
        )
        self._check()

    def set_nameid(self, format: str, encrypt: bool = False) -> Self:
        """Set the SAML NameID format URI and optional encryption flag."""
        self.nameid_format = format
        self.encrypt_nameid = YesNo.YES if encrypt else YesNo.NO
        return self

    def set_security(
        self,
        sign_assertions: bool = False,
        sign_authn_requests: bool = False,
        sign_messages: bool = False,
        sign_logout_requests: bool = False,
        sign_logout_responses: bool = False,
        encrypt_assertions: bool = False,
    ) -> Self:
        """Configure SAML signature and assertion encryption settings."""
        self.sign_assertions = YesNo.YES if sign_assertions else YesNo.NO
        self.sign_authn_requests = YesNo.YES if sign_authn_requests else YesNo.NO
        self.sign_messages = YesNo.YES if sign_messages else YesNo.NO
        self.sign_logout_requests = YesNo.YES if sign_logout_requests else YesNo.NO
        self.sign_logout_responses = YesNo.YES if sign_logout_responses else YesNo.NO
        self.encrypt_assertions = YesNo.YES if encrypt_assertions else YesNo.NO
        return self

    def set_provisioning(
        self,
        group_name: str,
        disabled_user_group: UserGroup,
        user_username: str | None = None,
        user_lastname: str | None = None,
        groups: SamlProvisionGroup | list[SamlProvisionGroup] | None = None,
        media: SamlProvisionMedia | list[SamlProvisionMedia] | None = None,
    ) -> Self:
        """Enable JIT provisioning.

        Args:
            group_name: SAML attribute carrying group membership values.
            disabled_user_group: UserGroup to place deprovisioned users into.
                For a real lockout set that group's users_status to DISABLED.
            user_username: SAML attribute mapped to the user's first name.
            user_lastname: SAML attribute mapped to the user's last name.
            groups: SamlProvisionGroup or list defining SAML group → Zabbix role/group mappings.
            media: SamlProvisionMedia or list defining SAML attribute → Zabbix media mappings.
        """
        self.provision_status = ProvisionStatus.ENABLED
        self.group_name = group_name
        self.disabled_user_group = disabled_user_group.name
        self.user_username = user_username
        self.user_lastname = user_lastname
        if groups is not None:
            self.link_provision_group(groups)
        if media is not None:
            self.link_provision_media(media)
        return self

    def set_case_sensitive(self, enabled: bool) -> Self:
        """Enable or disable case-sensitive SAML login matching."""
        self.saml_case_sensitive = YesNo.YES if enabled else YesNo.NO
        return self

    def link_provision_group(
        self,
        group: SamlProvisionGroup | list[SamlProvisionGroup],
    ) -> Self:
        """Link a SAML group-to-role mapping. Accepts SamlProvisionGroup or list. Raises on duplicate."""
        items = group if isinstance(group, list) else [group]
        for item in items:
            if any(existing.name == item.name for existing in self.provision_groups):
                raise ValueError(
                    f"Duplicate provision_group '{item.name}'"
                )
            self.provision_groups.append(item)
        return self

    def link_provision_media(
        self,
        media: SamlProvisionMedia | list[SamlProvisionMedia],
    ) -> Self:
        """Link a SAML attribute-to-media mapping. Accepts SamlProvisionMedia or list."""
        items = media if isinstance(media, list) else [media]
        for item in items:
            if any(existing.name == item.name for existing in self.provision_media):
                raise ValueError(
                    f"Duplicate provision_media '{item.name}'"
                )
            self.provision_media.append(item)
        return self

    def _check(self) -> None:
        if self.provision_status == ProvisionStatus.ENABLED:
            if not self.group_name:
                raise ValueError(
                    "SamlProvider.group_name: required when provision_status is ENABLED"
                )
            if not self.disabled_user_group:
                raise ValueError(
                    "SamlProvider.disabled_user_group: required when provision_status is ENABLED"
                )
            if not self.provision_groups:
                raise ValueError(
                    "SamlProvider.provision_groups: required when provision_status is ENABLED"
                )
        else:
            if self.provision_groups or self.provision_media:
                raise ValueError(
                    "SamlProvider: provision_groups/provision_media set but provisioning is disabled; "
                    "call set_provisioning() to enable JIT"
                )
