from typing import Self

from zbxtemplar.decree.DecreeEntity import DecreeEntity
from zbxtemplar.decree.UserGroup import UserGroup
from zbxtemplar.decree.User import UserMedia
from zbxtemplar.decree.constants import ProvisionStatus, ScimStatus
from zbxtemplar.dicts.Schema import SchemaField
from zbxtemplar.zabbix.ZbxEntity import YesNo


class SamlProvisionGroup(DecreeEntity):
    """SAML JIT provisioning group mapping managed by decree YAML."""

    _SCHEMA = [
        SchemaField("name", optional=False, description="SAML group attribute value to match."),
        SchemaField("role", optional=False, description="Zabbix role name to resolve via role.get."),
        SchemaField("user_groups", str_type="list[UserGroup]",
                    description="Zabbix user groups to attach to provisioned users.",
                    type=list[UserGroup]),
    ]

    def __init__(self, name: str, role: str, user_groups: list[UserGroup | str] | None = None):
        if not role:
            raise ValueError(
                f"SamlProvisionGroup '{name}': role must not be empty"
            )
        self.name = name
        self.role = role
        self.user_groups = []
        for group in user_groups or []:
            self.add_user_group(group)

    def add_user_group(self, group: UserGroup | str):
        user_group = group if isinstance(group, UserGroup) else UserGroup(group)
        if any(existing.name == user_group.name for existing in self.user_groups):
            raise ValueError(
                f"Duplicate user_group '{user_group.name}' on SAML provision group '{self.name}'"
            )
        self.user_groups.append(user_group)
        return self

    def user_groups_to_list(self):
        return [group.name for group in self.user_groups]

    def to_dict(self) -> dict:
        if not self.user_groups:
            raise ValueError(
                f"SamlProvisionGroup '{self.name}': user_groups must contain at least one group"
            )
        return super().to_dict()

    @classmethod
    def validate(cls, data: dict) -> bool:
        super().validate(data)
        if not data.get("role"):
            raise ValueError(
                f"SamlProvisionGroup '{data.get('name')}': role must not be empty"
            )
        if not data.get("user_groups"):
            raise ValueError(
                f"SamlProvisionGroup '{data.get('name')}': user_groups must contain at least one group"
            )
        return True


class SamlProvisionMedia(UserMedia):
    """SAML JIT provisioning media mapping managed by decree YAML."""

    _SCHEMA = [
        SchemaField("name", optional=False, type=str, description="SAML provision media mapping name."),
        SchemaField("attribute", optional=False, type=str,
                    description="SAML attribute to copy into sendto at provisioning time."),
        *[f for f in UserMedia._SCHEMA if f.key != "sendto"],
    ]

    def __init__(self, name: str, media_type: str, attribute: str):
        self.name = name
        self.type = media_type
        self.attribute = attribute


class SamlProvider(DecreeEntity):
    """Zabbix SAML userdirectory entry managed by decree YAML."""

    _SCHEMA = [
        SchemaField("idp_entityid", optional=False, description="Identity provider entity ID."),
        SchemaField("sp_entityid", optional=False, description="Zabbix service provider entity ID."),
        SchemaField("sso_url", optional=False, description="Identity provider SSO URL."),
        SchemaField("slo_url", description="Identity provider SLO URL."),
        SchemaField("username_attribute", optional=False,
                    description="SAML attribute to use as the Zabbix username."),


        SchemaField("nameid_format", description="SAML NameID format URI."),
        SchemaField("encrypt_nameid", str_type="YES or NO", description="Encrypt SAML NameID flag.",
                    type=YesNo),


        SchemaField("encrypt_assertions", str_type="YES or NO",
                    description="Encrypt SAML assertions flag.",
                    type=YesNo),
        SchemaField("sign_messages", str_type="YES or NO", description="Sign SAML messages flag.",
                    type=YesNo),
        SchemaField("sign_assertions", str_type="YES or NO", description="Sign SAML assertions flag.",
                    type=YesNo),
        SchemaField("sign_authn_requests", str_type="YES or NO",
                    description="Sign SAML authn requests flag.",
                    type=YesNo),
        SchemaField("sign_logout_requests", str_type="YES or NO",
                    description="Sign SAML logout requests flag.",
                    type=YesNo),
        SchemaField("sign_logout_responses", str_type="YES or NO",
                    description="Sign SAML logout responses flag.",
                    type=YesNo),


        SchemaField("provision_status", str_type="ProvisionStatus",
                    description="JIT provisioning status: DISABLED or ENABLED.",
                    type=ProvisionStatus),
        SchemaField("group_name", description="SAML attribute carrying group membership."),
        SchemaField("user_username", description="SAML attribute to use as the user's first name."),
        SchemaField("user_lastname", description="SAML attribute to use as the user's last name."),
        SchemaField("disabled_user_group", str_type="UserGroup",
                    description="Zabbix user group to place deprovisioned SAML users into. Note: This group must be configured with gui_access=DISABLED or users_status=DISABLED.",
                    type=UserGroup),
        SchemaField("provision_groups", str_type="list[SamlProvisionGroup]",
                    description="SAML group to Zabbix role/user group mappings.",
                    type=list[SamlProvisionGroup]),
        SchemaField("provision_media", str_type="list[SamlProvisionMedia]",
                    description="SAML attribute to Zabbix media mappings.",
                    type=list[SamlProvisionMedia]),


        SchemaField("scim_status", str_type="ScimStatus",
                    description="SCIM provisioning status: DISABLED or ENABLED.",
                    type=ScimStatus),


        SchemaField("saml_case_sensitive", str_type="YES or NO",
                    description="SAML case-sensitive login flag applied via authentication.update.",
                    type=YesNo),
    ]

    def __init__(
        self,
        idp_entityid: str,
        sp_entityid: str,
        sso_url: str,
        username_attribute: str,
        slo_url: str | None = None,
    ):
        self.idp_entityid = idp_entityid
        self.sp_entityid = sp_entityid
        self.sso_url = sso_url
        self.username_attribute = username_attribute
        if slo_url is not None:
            self.slo_url = slo_url

        self.sign_assertions = YesNo.NO
        self.sign_authn_requests = YesNo.NO
        self.sign_messages = YesNo.NO
        self.sign_logout_requests = YesNo.NO
        self.sign_logout_responses = YesNo.NO
        self.encrypt_assertions = YesNo.NO
        self.encrypt_nameid = YesNo.NO

        self.provision_status = ProvisionStatus.DISABLED
        self.scim_status = ScimStatus.DISABLED
        self.group_name = None
        self.user_username = None
        self.user_lastname = None
        self.disabled_user_group = None
        self.provision_groups = []
        self.provision_media = []
        self.saml_case_sensitive = YesNo.YES

    def set_nameid(self, format: str, encrypt: bool = False) -> Self:
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
        self.provision_status = ProvisionStatus.ENABLED
        self.group_name = group_name
        self.disabled_user_group = disabled_user_group
        self.user_username = user_username
        self.user_lastname = user_lastname
        if groups is not None:
            self.add_provision_group(groups)
        if media is not None:
            self.add_provision_media(media)
        return self

    def set_case_sensitive(self, enabled: bool) -> Self:
        self.saml_case_sensitive = YesNo.YES if enabled else YesNo.NO
        return self

    def add_provision_group(
        self,
        group: SamlProvisionGroup | list[SamlProvisionGroup],
    ) -> Self:
        items = group if isinstance(group, list) else [group]
        for item in items:
            if any(existing.name == item.name for existing in self.provision_groups):
                raise ValueError(
                    f"Duplicate provision_group '{item.name}'"
                )
            self.provision_groups.append(item)
        return self

    def add_provision_media(
        self,
        media: SamlProvisionMedia | list[SamlProvisionMedia],
    ) -> Self:
        items = media if isinstance(media, list) else [media]
        for item in items:
            if any(existing.name == item.name for existing in self.provision_media):
                raise ValueError(
                    f"Duplicate provision_media '{item.name}'"
                )
            self.provision_media.append(item)
        return self

    def provision_groups_to_list(self):
        return [group.to_dict() for group in self.provision_groups]

    def provision_media_to_list(self):
        return [media.to_dict() for media in self.provision_media]

    def disabled_user_group_to_list(self):
        if self.disabled_user_group is None:
            return None
        return self.disabled_user_group.name

    def to_dict(self) -> dict:
        self._check()
        return super().to_dict()

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        obj = super().from_dict(data)
        obj._check()
        return obj

    def _check(self):
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
