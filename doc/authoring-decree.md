# Authoring Decree

This is the narrative guide for composing a `DecreeModule` — user groups, users, media, API tokens, SAML JIT provisioning, host encryption, and module-level macros.

For the compact lookup version, see the reference pages: [`decree.md`](./reference/decree.md), [`saml_encryption.md`](./reference/saml_encryption.md).

Actions are also authored inside a `DecreeModule`, but they have enough surface area to warrant their own page: [Authoring Actions](./authoring-actions.md).

For CLI flags, `--param`, and `--context` details see [CLI Reference](./cli-reference.md).

## Why Decree Needs Code

Zabbix mixes declarative and live-state objects. Templates and hosts fit the import/export model cleanly. Users, permissions, SAML providers, alert routing, and per-host encryption do not — they are live API state that drifts the moment someone clicks a checkbox in the UI.

- **Credentials in git is a non-starter.** `${ENV_VAR}` placeholders keep secrets in the environment; a missing variable hard-aborts before any API call lands.
- **Permissions are combinatorial.** Ten teams × three environments × four host groups × two permission levels. Clicking is untenable; a loop is trivial.
- **SAML is hard to configure from the UI and harder to review.** JIT provisioning rules — attribute names, group mappings, media provisioning — need the same diff-driven review as monitoring code.
- **Host encryption drifts silently.** PSK secrets are write-only in the Zabbix API; without code-driven apply, you never know what is really set.

## The Shape of a DecreeModule

```python
from zbxtemplar.modules import DecreeModule
from zbxtemplar.decree import GuiAccess, Permission, Severity, Token
from zbxtemplar.catalog.zabbix_7_4 import MediaType, UserRole


class MyDecree(DecreeModule):
    def compose(self, alert_email: str = "alerts@example.com"):

        ops = self.add_user_group("Operations", gui_access=GuiAccess.INTERNAL)
        ops.link_host_group("Linux Servers", Permission.READ)

        user = self.add_user("zbx-ops", role=UserRole.ADMIN)
        user.link_group(ops)
        user.add_media(MediaType.EMAIL, alert_email).set_severity(
            [Severity.HIGH, Severity.DISASTER]
        )
        user.set_token(
            "zbx-ops-api",
            store_at=".secrets/zbx-ops-api.token",
            expires_at=Token.EXPIRES_NEVER,
        )
```

`compose()` is the module contract; its signature becomes the `--param` surface. Builders on `self` construct, register, and return the decree object — you then mutate it to add permissions, media, SAML rules, action conditions and operations, etc.

- `add_user_group(name, ...)` → `UserGroup`
- `add_user(username, role)` → `User`
- `set_saml(...)` → `SamlProvider`
- `set_encryption_defaults(...)` → `Encryption`
- `add_host_encryption(host, ...)` → `HostEncryption`
- `add_trigger_action(name)` → `TriggerAction`
- `add_autoregistration_action(name)` → `AutoregistrationAction`

Duplicate user groups, users, SAML providers, actions, or host encryption entries raise `ValueError`.

## User Groups and Permissions

```python
from zbxtemplar.decree import GuiAccess, UsersStatus, Permission

group = self.add_user_group(
    "Ops Team",
    gui_access=GuiAccess.INTERNAL,    # DEFAULT, INTERNAL, LDAP, DISABLED
    users_status=UsersStatus.ENABLED, # ENABLED, DISABLED
)

group.link_host_group("Linux servers", Permission.READ)
group.link_host_group(self.context.get_host_group("Prod"), Permission.READ_WRITE)
group.link_template_group("My Templates", Permission.READ)
```

`Permission`: `NONE`, `READ`, `READ_WRITE`. Both name strings and `HostGroup` / `TemplateGroup` objects from `--context` are accepted.

## Users, Media, Tokens

```python
from zbxtemplar.decree import Severity, Token
from zbxtemplar.catalog.zabbix_7_4 import MediaType, UserRole

user = self.add_user("alice", role=UserRole.ADMIN)
# UserRole: SUPER_ADMIN, ADMIN, USER, GUEST

user.set_password("${ALICE_PASSWORD}")   # pulled from env at executor time
user.link_group(group)

media = user.add_media(MediaType.EMAIL, "alice@example.com")
media.set_severity([Severity.HIGH, Severity.DISASTER])
media.set_period("1-7,00:00-24:00")
user.add_media(MediaType.SLACK, "#alerts")
```

Common `MediaType` constants: `EMAIL`, `SLACK`, `TELEGRAM`, `MS_TEAMS`, `MS_TEAMS_WORKFLOW`, `PAGERDUTY`, `OPSGENIE`, `DISCORD`, `SMS`, `MATTERMOST`, `ROCKET_CHAT`, `PUSHOVER`, `VICTOROPS`. Full list in `zbxtemplar.catalog.zabbix_7_4.MediaType`.

### API tokens

Token provisioning has deliberate guardrails — see [Security & Safety](./security.md#token-provisioning-safety):

```python
user.set_token(
    "zbx-ops-api",
    store_at=".secrets/zbx-ops-api.token",   # or Token.STDOUT
    expires_at=Token.EXPIRES_NEVER,                  # or a future unix timestamp
    force=True,                              # regenerate if it already exists
)
```

`store_at` is required (no accidental leaks to stdout); writing to an existing file is refused unless `force=True`.

## SAML JIT Provisioning

One SAML provider per deployment. `set_saml()` called twice in the same module is an error — SAML is declarative global state.

```python
saml = self.set_saml(
    idp_entityid="http://www.okta.com/example",
    sp_entityid="zabbix",
    sso_url="https://example.okta.com/app/sso/saml",
    username_attribute="usrEmail",
    slo_url=None,
)

saml.set_security(sign_assertions=True, encrypt_assertions=True)
saml.set_case_sensitive(True)
```

### JIT provisioning rules

```python
from zbxtemplar.decree import SamlProvisionGroup, SamlProvisionMedia, UsersStatus

# Lockout group: gui_access=DISABLED alone blocks frontend but NOT API tokens.
# Use users_status=DISABLED for a full lockout.
disabled = self.add_user_group(
    "SAML Deprovisioned",
    gui_access=GuiAccess.DISABLED,
    users_status=UsersStatus.DISABLED,
)

saml.set_provisioning(
    group_name="groups",
    disabled_user_group=disabled,
    user_username="firstName",
    user_lastname="lastName",
    groups=SamlProvisionGroup("zabbix-admins", UserRole.SUPER_ADMIN, [ops]),
    media=SamlProvisionMedia("Email", MediaType.EMAIL, "email"),
)

saml.add_provision_group(SamlProvisionGroup("zabbix-users", UserRole.USER, [ops]))
saml.add_provision_media(SamlProvisionMedia("Slack", MediaType.SLACK, "slackHandle"))
```

`SamlProvisionGroup(saml_group_name, role, user_groups)` maps a SAML group to a Zabbix role and a list of user groups.

`SamlProvisionMedia(name, media_type, attribute)` provisions a media entry from a SAML attribute.

SAML configuration is validated before it reaches Zabbix — required fields, provisioning dependencies, role/group/media name resolution. Mistakes fail pre-flight, not halfway through an apply. See [Security & Safety — SAML JIT Provisioning](./security.md#saml-jit-provisioning).

## Host Encryption

Host communication security (PSK, TLS certs, unencrypted) is declarative:

```python
defaults = self.set_encryption_defaults(
    connect_unencrypted=True,
    accept_unencrypted=False,
)

enc = self.add_host_encryption(
    self.context.get_host("my-host"),
    connect_unencrypted=False,
    accept_unencrypted=True,
)
enc.set_psk(connect=True, accept=True, identity="psk_id", psk="${PSK_SECRET}")
enc.set_cert(connect=True, accept=True, issuer="CN=CA", subject="CN=my-host")
```

PSK secrets are write-only in Zabbix (the API never reads them back), so PSK-mode hosts are always updated on apply to prevent drift. Always pass PSK values through `${ENV_VAR}` to keep them out of git. See [Security & Safety — Host Encryption](./security.md#host-encryption).

## Module-Level Macros

`DecreeModule` (and `TemplarModule`) support global macros. They become `set_macro` entries in the output and are applied as Zabbix global macros:

```python
from zbxtemplar.zabbix import MacroType

self.add_macro("DB_PASSWORD", "${ZBX_DB_PASSWORD}", "DB password",
               MacroType.SECRET_TEXT)
```

`MacroType`: `TEXT` (default), `SECRET_TEXT` (alias: `SECRET`), `VAULT`.

## Validating Against Existing State

`--context` loads previously generated or exported YAML and exposes it as `self.context`. Typed lookups raise `ValueError` on a missing name:

```python
class MyDecree(DecreeModule):
    def compose(self):
        prod = self.context.get_host_group("Production")
        ops = self.context.get_user_group("Operations")
```

Group and user membership references accept both name strings and typed `--context` objects. See [CLI Reference — Context Files](./cli-reference.md#context-files).

## Names Now, IDs at Apply Time

Decree YAML references Zabbix objects by name, never by ID. This is the rule across every decree section:

- User group permissions reference host groups and template groups by name
- User membership references user groups by name
- User media references media types by name
- SAML JIT rules reference roles, user groups, and media types by name
- Host encryption references the host by name
- Action conditions reference host groups, hosts, triggers, templates by name
- Action operations reference user groups, users, media types by name

The executor resolves those names to live Zabbix IDs at apply time. That is what makes decree YAML reviewable in a PR and portable across dev, staging, and prod — you never have to pre-fetch an ID table, and the same YAML applies cleanly to any Zabbix instance where the referenced names exist.

This is the apply-time half of the two-stage safety model; the generation-time half is `--context`. Together they catch typos early (generation time) and bind the configuration to the real environment late (apply time) — see [Security & Safety — Two-Stage Validation Model](./security.md#two-stage-validation-model).

## Output

One combined file:

```bash
zbxtemplar decree_module.py -o decree.yml --context templates.yml
```

Or split per section:

```bash
zbxtemplar decree_module.py \
  --user-groups-output user_groups.yml \
  --users-output users.yml \
  --saml-output saml.yml \
  --actions-output actions.yml \
  --encryption-output encryption.yml
```

## Practical Advice

- Keep module logic inside `compose()`. The constructor is not the authoring contract; the `compose()` signature is.
- Always route secrets (`${ENV_VAR}`), never literals. A missing variable hard-aborts before any mutation — that is the intended safety net.
- Use `--context` to validate cross-artifact references (host groups coming from the monitoring module, users coming from an earlier decree) at generation time.
- SAML and encryption are declarative global state — treat them like config files, not like scripts. "Last apply wins" is the model.
