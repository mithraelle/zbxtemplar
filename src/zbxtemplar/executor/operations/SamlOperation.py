from zabbix_utils import APIRequestError

from zbxtemplar.decree import Severity
from zbxtemplar.decree.saml import SamlProvider
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log
from zbxtemplar.zabbix.ZbxEntity import YesNo


_IDP_TYPE_SAML = 2

_OPTIONAL_STR_FIELDS = (
    "slo_url", "nameid_format",
    "group_name", "user_username", "user_lastname",
)
_YESNO_FIELDS = (
    "encrypt_nameid", "encrypt_assertions",
    "sign_assertions", "sign_authn_requests", "sign_messages",
    "sign_logout_requests", "sign_logout_responses",
)


class SamlOperation(Executor):
    def __init__(self, spec: SamlProvider, api, base_dir=None):
        super().__init__(spec, api, base_dir)

    def _validate(self):
        pass

    @staticmethod
    def _yesno(value) -> int | None:
        if value is None:
            return None
        return 1 if value == YesNo.YES else 0

    def _build_provision_groups(self, provider, roles, ugroups):
        result = []
        for g in provider.provision_groups:
            if g.role not in roles:
                raise ValueError(f"Role '{g.role}' not found in Zabbix")
            user_groups = []
            for ug in g.user_groups:
                if ug.name not in ugroups:
                    raise ValueError(f"User group '{ug.name}' not found in Zabbix")
                user_groups.append({"usrgrpid": ugroups[ug.name]})
            result.append({
                "name": g.name,
                "roleid": roles[g.role],
                "user_groups": user_groups,
            })
        return result

    def _build_provision_media(self, provider, media_types):
        result = []
        for m in provider.provision_media:
            if m.type not in media_types:
                raise ValueError(f"Media type '{m.type}' not found in Zabbix")
            entry = {
                "name": m.name,
                "mediatypeid": media_types[m.type],
                "attribute": m.attribute,
            }
            if m.active is not None:
                entry["active"] = int(m.active)
            if m.severity is not None:
                entry["severity"] = Severity.mask(m.severity)
            if m.period is not None:
                entry["period"] = m.period
            result.append(entry)
        return result

    def _build_params(self, provider, roles, ugroups, media_types):
        params = {
            "name": "SAML",
            "idp_type": _IDP_TYPE_SAML,
            "idp_entityid": provider.idp_entityid,
            "sp_entityid": provider.sp_entityid,
            "sso_url": provider.sso_url,
            "username_attribute": provider.username_attribute,
        }
        for field in _OPTIONAL_STR_FIELDS:
            value = getattr(provider, field, None)
            if value is not None:
                params[field] = value

        for field in _YESNO_FIELDS:
            v = self._yesno(getattr(provider, field, None))
            if v is not None:
                params[field] = v

        if provider.provision_status is not None:
            params["provision_status"] = int(provider.provision_status)
        if provider.scim_status is not None:
            params["scim_status"] = int(provider.scim_status)

        if provider.provision_groups:
            params["provision_groups"] = self._build_provision_groups(provider, roles, ugroups)
        if provider.provision_media:
            params["provision_media"] = self._build_provision_media(provider, media_types)

        return params

    def execute(self):
        provider = self._spec
        roles = {r["name"]: r["roleid"] for r in self._api.role.get(output=["roleid", "name"])}
        ugroups = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}
        media_types = {m["name"]: m["mediatypeid"] for m in self._api.mediatype.get(output=["mediatypeid", "name"])}
        existing = self._api.userdirectory.get(
            filter={"idp_type": _IDP_TYPE_SAML},
            output=["userdirectoryid"],
        )
        log.lookup_end("saml", count=len(existing))

        params = self._build_params(provider, roles, ugroups, media_types)

        disabled_usrgrpid = None
        if provider.disabled_user_group is not None:
            name = provider.disabled_user_group.name
            if name not in ugroups:
                raise ValueError(f"User group '{name}' not found in Zabbix")
            disabled_usrgrpid = ugroups[name]

        if existing:
            userdirectoryid = existing[0]["userdirectoryid"]
            params["userdirectoryid"] = userdirectoryid
            del params["idp_type"]
            try:
                self._api.userdirectory.update(**params)
            except APIRequestError as e:
                raise ExecutorApiError(f"Failed to update SAML userdirectory: {e}") from e
            log.entity_end(
                "saml", action="update",
                id=userdirectoryid, idp_entityid=provider.idp_entityid,
                provision_groups=len(provider.provision_groups or []),
                provision_media=len(provider.provision_media or []),
            )
        else:
            try:
                result = self._api.userdirectory.create(**params)
            except APIRequestError as e:
                raise ExecutorApiError(f"Failed to create SAML userdirectory: {e}") from e
            userdirectoryid = (result or {}).get("userdirectoryids", [None])[0]
            log.entity_end(
                "saml", action="create",
                id=userdirectoryid, idp_entityid=provider.idp_entityid,
                provision_groups=len(provider.provision_groups or []),
                provision_media=len(provider.provision_media or []),
            )

        self._enable_saml_authentication(provider, disabled_usrgrpid)

    def _enable_saml_authentication(self, provider, disabled_usrgrpid):
        auth_params = {"saml_auth_enabled": 1}
        if provider.provision_status is not None:
            auth_params["saml_jit_status"] = int(provider.provision_status)
        if disabled_usrgrpid is not None:
            auth_params["disabled_usrgrpid"] = disabled_usrgrpid
        case_sensitive = self._yesno(provider.saml_case_sensitive)
        if case_sensitive is not None:
            auth_params["saml_case_sensitive"] = case_sensitive
        try:
            self._api.authentication.update(**auth_params)
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to enable SAML authentication: {e}") from e
        log.entity_end("saml_auth", action="update", **auth_params)