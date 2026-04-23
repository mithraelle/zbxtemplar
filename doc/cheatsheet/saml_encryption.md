# SAML & Host Encryption

`self.*` calls below are `DecreeModule` methods called from inside `compose()`.

## Imports

```python
from zbxtemplar.decree import SamlProvisionGroup, SamlProvisionMedia, GuiAccess, UsersStatus
from zbxtemplar.catalog.zabbix_7_4 import MediaType, UserRole
```

## SAML

One SAML provider per deployment — SAML declares desired state, so the last applied scroll
wins. Calling `set_saml()` twice within the same module raises an error.

```python
saml = self.set_saml(
    idp_entityid="http://www.okta.com/example",
    sp_entityid="zabbix",
    sso_url="https://example.okta.com/app/sso/saml",
    username_attribute="usrEmail",   # SAML attribute used as Zabbix username
    slo_url=None,                    # SLO endpoint URL (optional)
)
```

### Security flags

All default to `False`.

```python
saml.set_security(
    sign_assertions=True,
    sign_authn_requests=False,
    sign_messages=False,
    sign_logout_requests=False,
    sign_logout_responses=False,
    encrypt_assertions=True,
    encrypt_nameid=False,
)
```

### Username case sensitivity

```python
saml.set_case_sensitive(True)   # default False
```

### JIT provisioning

```python
# Group for deprovisioned users. users_status=DISABLED is required for full lockout;
# gui_access=DISABLED alone blocks frontend but NOT API token access.
disabled_group = self.add_user_group(
    "SAML Deprovisioned",
    gui_access=GuiAccess.DISABLED,
    users_status=UsersStatus.DISABLED,
)

saml.set_provisioning(
    group_name="groups",                  # SAML attribute carrying group membership
    disabled_user_group=disabled_group,   # UserGroup object or name string
    user_username="firstName",            # SAML attribute → Zabbix user firstname
    user_lastname="lastName",
    user_name=None,                       # optional: maps to Zabbix user name field
    groups=SamlProvisionGroup("zabbix-admins", UserRole.SUPER_ADMIN, [ops_group]),
    media=SamlProvisionMedia("Email", MediaType.EMAIL, "email"),
)

# Add more provision groups / media after set_provisioning:
saml.add_provision_group(SamlProvisionGroup("zabbix-users", UserRole.USER, [ops_group]))
saml.add_provision_media(SamlProvisionMedia("Slack", MediaType.SLACK, "slackHandle"))
```

`SamlProvisionGroup(saml_group_name, role, user_groups)` — maps a SAML group to a Zabbix role
and a list of Zabbix user groups (UserGroup objects or name strings).

`SamlProvisionMedia(name, media_type, attribute)` — provisions a media entry from a SAML attribute.

## Host encryption

```python
# Module-level defaults merged into every host encryption entry
defaults = self.set_encryption_defaults(
    connect_unencrypted=True,
    accept_unencrypted=False,
)

# Per-host settings (chain .set_psk() / .set_cert() as needed)
enc = self.add_host_encryption(
    self.context.get_host("my-host"),   # or host name string
    connect_unencrypted=False,
    accept_unencrypted=True,
)
enc.set_psk(connect=True, accept=True, identity="psk_id", psk="${PSK_SECRET}")
enc.set_cert(connect=True, accept=True, issuer="CN=CA", subject="CN=my-host")
```

PSK requires both `identity` and `psk`.
Cert requires at least one of `issuer` or `subject`.
`EncryptionMode` values: UNENCRYPTED, PSK, CERT.