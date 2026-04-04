# Executor Guide

## Purpose

`zbxtemplar-exec` applies generated artifacts to a live Zabbix instance.

It handles two broad cases:

- importing Zabbix-native YAML
- applying decree YAML for stateful objects such as users, groups, actions, and host encryption

## Installation

The executor depends on the optional `executor` extra:

```bash
pip install '.[executor]'
```

## Authentication

Connection inputs:

- `--url` or `ZABBIX_URL`
- `--token` or `ZABBIX_TOKEN`
- `--user` or `ZABBIX_USER`
- `--password` or `ZABBIX_PASSWORD`

Token auth is preferred for automation:

```bash
zbxtemplar-exec apply templates.yml \
  --url https://zabbix.example.com \
  --token "$ZABBIX_TOKEN"
```

Password auth is available for bootstrap cases:

```bash
zbxtemplar-exec apply templates.yml \
  --url https://zabbix.example.com \
  --user Admin \
  --password "$ZABBIX_PASSWORD"
```

## Commands

### `apply`

Imports Zabbix-native YAML through `configuration.import`.

```bash
zbxtemplar-exec apply templates.yml --url ... --token ...
```

### `decree`

Applies decree YAML sections in dependency order:

1. `user_group`
2. `add_user`
3. `actions`
4. `encryption`

```bash
zbxtemplar-exec decree decree.yml --url ... --token ...
```

The `encryption` section manages host communication security — PSK, TLS certificate, or unencrypted. This means encryption settings live in version-controlled code rather than being configured ad-hoc in the UI. It supports `host_defaults` for shared settings and per-host overrides:

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

Per-host keys fully replace defaults (no merging of individual fields). A host entry with only `host` inherits all defaults. Hosts are matched by technical name against the live Zabbix instance.

PSK secrets are write-only in Zabbix (the API never returns them), so PSK-mode hosts are always updated to prevent drift. Use `${ENV_VAR}` for PSK values to keep them out of committed files.

### `add_user`

Convenience wrapper for user-only YAML.

```bash
zbxtemplar-exec add_user service-account.yml --url ... --token ...
```

Token provisioning is configured inside each user:

```yaml
add_user:
  - username: api-reader
    role: User role
    token:
      name: api-reader-token
      expires_at: NEVER
      store_at: .secrets/api-reader.token
    force_token: true
```

Rules worth knowing:

- `token` must be an object, not a string
- `token.name` is required
- create-time provisioning requires `token.expires_at`
- `token.expires_at` accepts a Unix timestamp or `NEVER`
- each token needs an output sink via `store_at` (a file path or `STDOUT`)
- existing tokens are skipped unless `force_token: true` is set, in which case they are updated in place and re-enabled
- `force_token: true` generates a new secret for an existing token and ensures it is enabled; this is an aggressive operation, not a graceful coordinated rotation

Safety rails on token output:

- `store_at` is required — no accidental token-to-stdout leaks
- duplicate `store_at` paths in one run are rejected (prevents two users silently overwriting each other's token file)
- writing to an already existing output file is rejected (prevents silent overwrite of a previously provisioned token)
- token ownership is validated (will not touch a token belonging to the wrong user)

### `set_macro`

Sets global macros inline or from a file.

```bash
zbxtemplar-exec set_macro SNMP_COMMUNITY public --url ... --token ...
zbxtemplar-exec set_macro macros.yml --url ... --token ...
```

Global macros support three storage types via the `type` field:

| Type | Behavior |
|------|----------|
| `text` | Default. Value stored and visible in the Zabbix UI. |
| `secret` | Value stored but masked in the UI. Cannot be read back via API. |
| `vault` | Value is a Vault path. Zabbix fetches the actual secret from HashiCorp Vault at runtime. |

Example macro file:

```yaml
- name: SNMP_COMMUNITY
  value: public

- name: DB_PASSWORD
  value: ${DB_PASSWORD}
  type: secret

- name: API_KEY
  value: vault:secret/data/myapp:api_key
  type: vault
```

Secret and vault macros keep credentials out of the Zabbix UI. Combined with `${ENV_VAR}` interpolation, the actual secret values never appear in committed YAML either.

### `set_super_admin`

Updates the built-in super admin password:

```bash
zbxtemplar-exec set_super_admin --new-password "$ZBX_ADMIN_PASSWORD" --url ... --password ...
```

Every Zabbix install ships with `Admin/zabbix` as the default credentials. In a scroll pipeline, `set_super_admin` belongs in the `bootstrap` stage so the default password is changed before anything else runs.

### `scroll`

Runs a staged deployment file using the built-in pipeline:

- `bootstrap`
- `templates`
- `state`

```bash
zbxtemplar-exec scroll deploy.scroll.yml --url ... --token ...
zbxtemplar-exec scroll deploy.scroll.yml --from-stage templates --url ... --token ...
zbxtemplar-exec scroll deploy.scroll.yml --only-stage state --url ... --token ...
```

## Environment Variable Interpolation

Sensitive string values may contain `${VAR_NAME}` placeholders. This is a deliberate security design: secrets live in environment variables, never in YAML files committed to git.

Before any mutating API call, the executor performs a pre-flight scan of all values. If any referenced environment variable is missing, execution aborts immediately — no partial state, no half-applied changes. A missing variable is a hard abort, never an empty-string substitution.

This applies to:

- `set_super_admin`
- `set_macro`
- decree user handling
- encryption PSK values
- scroll inputs that feed those actions

For scrolls, the pre-flight scan runs across all stages before the first stage executes. This means a typo in a stage-3 secret is caught before stage 1 begins.

## How Name Resolution Works

Decree files reference Zabbix objects by name. The executor resolves those names to live IDs at runtime.

Examples:

- user group name -> `usrgrpid`
- user name -> `userid`
- media type name -> `mediatypeid`
- host group name -> `groupid`
- template name -> `templateid`

This keeps decree YAML readable and reviewable.

## Recommended Operating Model

Use a test Zabbix instance first, then production.

That is the intended safety model for this project:

1. generate artifacts
2. review them
3. validate them in test
4. re-run against production

The executor is designed around idempotent re-apply more than around a separate dry-run engine.

## Current Operational Caveats

- Partial progress logging could be clearer during long or multi-step applies.
