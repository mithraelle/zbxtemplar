# Security & Operational Safety

zbxtemplar is designed so that deploying monitoring configuration cannot accidentally leak credentials, partially apply state, or silently ignore misconfiguration.

This page consolidates the safety features that are built into both the generator and executor.

## Secret Management

### Environment Variable Interpolation

Sensitive values use `${VAR_NAME}` placeholders in YAML. The actual secrets live in environment variables, never in files committed to git.

```yaml
set_macro:
  - name: DB_PASSWORD
    value: ${DB_PASSWORD}
    type: SECRET_TEXT
```

This is enforced by design:

- Missing environment variables cause a hard abort, never empty-string substitution.
- The executor runs a pre-flight scan of all values before any API call. If any variable is missing, nothing is touched.
- For scrolls, the scan covers all actions upfront — a missing variable in a late action is caught before the first action begins.

### Global Macro Types

Global macros support three storage types (values match Zabbix native export format):

| Type | Behavior |
|------|----------|
| `TEXT` | Default. Value is stored and visible in the Zabbix UI. |
| `SECRET_TEXT` | Value is stored but masked in the UI. Cannot be read back via API. |
| `VAULT` | Value is a Vault path. Zabbix fetches the actual secret from HashiCorp Vault at runtime. |

In Python code, `MacroType.SECRET` is an alias for `MacroType.SECRET_TEXT`.

```yaml
- name: API_KEY
  value: ${API_KEY}
  type: SECRET_TEXT

- name: CERT_PASSPHRASE
  value: vault:secret/data/certs:passphrase
  type: VAULT
```

Secret macros keep credentials hidden in the Zabbix web interface. Vault macros go further — the secret value never reaches Zabbix at all; Zabbix fetches it directly from HashiCorp Vault when needed.

## Host Encryption

The `encryption` decree section manages host communication security declaratively:

- **PSK** — pre-shared key with identity string
- **Certificate** — TLS with issuer/subject validation
- **Per-host overrides** on top of shared `host_defaults`

```yaml
encryption:
  host_defaults:
    connect: PSK
    accept: UNENCRYPTED, PSK
    psk_identity: shared_id
    psk: ${PSK_SECRET}
  hosts:
  - host: my-host
  - host: special-host
    connect: CERT
    accept: CERT
    issuer: CN=Root CA
    subject: CN=special-host
```

PSK secrets are write-only in Zabbix (the API never returns them), so PSK-mode hosts are always updated to prevent drift. Use `${ENV_VAR}` for PSK values to keep them out of version control.

Encryption settings are validated at parse time — invalid combinations fail before any API call.

## SAML JIT Provisioning

The `saml` decree section manages Zabbix SAML SSO and JIT provisioning declaratively. Required provider fields, provisioning dependencies, role names, user group names, and media type names are validated before the SAML directory is created or updated.

When JIT provisioning is enabled, `group_name`, `disabled_user_group`, and at least one `provision_groups` entry are required. The `disabled_user_group` is where Zabbix places deprovisioned SAML users — it only acts as a real lockout if you also declare that group with `users_status: DISABLED` in your user group configuration, which disables the member users entirely. `gui_access: DISABLED` alone blocks frontend login but does not revoke API token access; the executor wires the group into Zabbix authentication, but the lockout semantics are part of your declared user group configuration.

## Token Provisioning Safety

Token output has deliberate guardrails:

- `store_at` is required — no accidental token leaks to stdout
- Duplicate `store_at` paths in one run are rejected
- Writing to an already existing file is rejected (prevents silent overwrite)
- Token ownership is validated (will not touch a token belonging to the wrong user)
- `force_token` is explicitly labeled as a destructive operation — it regenerates the secret and re-enables the token

## Bootstrap Security

Every Zabbix installation ships with hardcoded default credentials (`Admin/zabbix`). The `set_super_admin` command exists to change this immediately.

In a scroll pipeline, this is configured as the `set_super_admin` action — the first thing that runs, before any templates are imported or users are created. The `current_password` field is required when changing the password.

```yaml
set_super_admin:
  password: ${ZBX_ADMIN_PASSWORD}
  current_password: zabbix
```

## Fail-Fast Validation

Errors are surfaced as early as possible, at the cheapest point in the pipeline:

| What | When | Effect |
|------|------|--------|
| Unknown YAML keys in decree files | Pre-flight | Hard error with Typo suggestions (`difflib`) |
| Missing required keys in decree files | Pre-flight | Hard error, no API calls |
| Unknown keys in scroll documents | Pre-flight | Hard error, no API calls |
| Unknown context file format | Load time | Hard error, no generation |
| Missing `${ENV_VAR}` references | Pre-flight | Hard abort before any mutation |
| Invalid encryption settings | Parse time | Validation error |
| Invalid SAML provisioning settings | Parse time / pre-flight | Validation error before SAML mutation |
| Python `and`/`or` on action conditions | Write time | `TypeError` with clear message |
| Macro not found on template/host | Generation time | `KeyError` |
| Name not found in Context | Generation time | `ValueError` |
| Invalid condition operators | Write time | Type error (scoped `Op` enums) |

The principle: mistakes surface at generation time or pre-flight, not against production during an incident.

## Two-Stage Validation Model

zbxtemplar validates configuration at two points:

**Generation time** — Context validates that referenced names (host groups, templates, users) exist in supplied YAML. Catches typos, missing references, and structural errors. This is a real check against a known baseline, not just syntax validation.

**Apply time** — The executor resolves names to live Zabbix IDs and applies changes. Catches objects that exist in config but not yet in the live instance.

Context is a snapshot, not a live connection. It cannot guarantee that the live Zabbix instance matches the YAML baseline. The intended safety model remains:

1. Generate artifacts
2. Review them (git diff)
3. Validate in a test Zabbix environment
4. Apply to production

This is the practical safety model for a tool operating against a stateful external system.
