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

Applies a configuration file to Zabbix. The type is auto-detected: Zabbix export, decree, or scroll.

```bash
zbxtemplar-exec apply config.yml --url ... --token ...
```

#### Apply: Zabbix Export

Imports Zabbix-native YAML through `configuration.import`.

#### Apply: Decree

Applies decree YAML sections in dependency order:

1. `user_group`
2. `add_user`
3. `actions`
4. `encryption`

The `decree` sections such as `actions` natively support loading from external YAML files. Passing a file path string instead of a nested dictionary allows you to manage and reload large action/trigger configurations independently.

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

#### Apply: Decree `add_user`

Token provisioning is configured inside each user in the `add_user` list:

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

#### Apply: Scroll

Runs an ordered deployment configuration file using the built-in action sequence:

- `set_super_admin`
- `set_macro`
- `apply`
- `decree`

```yaml
set_super_admin:
  password: ${ZBX_ADMIN_PASSWORD}
  current_password: zabbix
set_macro: macros.yml
apply: 
  - templates.yml
  - hosts.yml
decree: decree.yml
```

```bash
zbxtemplar-exec apply deploy.scroll.yml --url ... --token ...
zbxtemplar-exec apply deploy.scroll.yml --from-action apply --url ... --token ...
zbxtemplar-exec apply deploy.scroll.yml --only-action decree --url ... --token ...
```

### `set_macro`

Sets a global macro inline. When setting an inline macro, you can optionally specify its storage type using the `--type` flag.
(Note: To set macros from a file, use the `apply` command with a scroll or decree containing a `set_macro` action).

```bash
zbxtemplar-exec set_macro SNMP_COMMUNITY public --url ... --token ...
zbxtemplar-exec set_macro DB_PASSWORD "$DB_PASS" --type secret --url ... --token ...
```

Global macros support three storage types via the `type` field:

| Type | Behavior |
|------|----------|
| `text` | Default. Value stored and visible in the Zabbix UI. |
| `secret` | Value stored but masked in the UI. Cannot be read back via API. |
| `vault` | Value is a Vault path. Zabbix fetches the actual secret from HashiCorp Vault at runtime. |

Type values match the Zabbix native export format: `TEXT` (default), `SECRET_TEXT`, `VAULT`. Secret and vault macros keep credentials out of the Zabbix UI. Combined with `${ENV_VAR}` interpolation, the actual secret values never appear in committed YAML either.

### `set_super_admin`

Updates the currently authenticated super admin user — password, username, or both:

```bash
zbxtemplar-exec set_super_admin --new-password "$ZBX_NEW_PASSWORD" --current-password "$ZBX_CURRENT_PASSWORD" --url ... --password ...
```

When `--current-password` is omitted, the CLI falls back to the `--password` used for authentication. The `--username` flag optionally renames the admin account.

After a password change with session auth (not token), the executor automatically re-logs in with the new credentials so subsequent scroll actions continue working.

## Environment Variable Interpolation

Sensitive string values may contain `${VAR_NAME}` placeholders. This is a deliberate security design: secrets live in environment variables, never in YAML files committed to git.

Before any mutating API call, the executor performs a pre-flight scan of all values. If any referenced environment variable is missing, execution aborts immediately — no partial state, no half-applied changes. A missing variable is a hard abort, never an empty-string substitution.

This applies to:

- `set_super_admin`
- `set_macro`
- decree user handling
- encryption PSK values
- scroll inputs that feed those actions

For scrolls, the pre-flight scan runs across all actions before the first action executes. This means a typo in the secret for a late action is caught before the first action begins.

## Schema Validation and Typo Assistance

The executor enforces schema correctness through a "Fail Fast" mechanism. Before applying your yaml, the `Schema` validator checks the entire parsed dictionary against internal schemas.

If an invalid key is detected (for example, `expire_at` instead of `expires_at`), execution halts immediately and the executor offers a typo suggestion using `difflib.get_close_matches`:

```
ValueError: Token: unknown key 'expire_at', did you mean 'expires_at'?
```

This prevents typos from silently dropping intended configuration and mutating your live production environment.

## How Name Resolution Works

Decree files reference Zabbix objects by name. The executor resolves those names to live IDs at runtime.

Examples:

- user group name -> `usrgrpid`
- user name -> `userid`
- media type name -> `mediatypeid`
- host group name -> `groupid`
- template name -> `templateid`

This keeps decree YAML readable and reviewable.

## Log Output

Every run emits a structured, sequenced event stream to stdout. Each line carries a `[NNN]` counter and a `event.type key=value` payload.

```
[001] run.start run_id=20260413T192659Z-1070 target=zabbix.example.com auth=token
[002] input.loaded path=deploy.scroll.yml sha256=3e61fbdc... bytes=256
[003] action.start name=set_macro items=3
[004] lookup.end type=global_macros count=1
[005] entity.end type=macro action=update result=ok name={$SNMP_COMMUNITY} value_redacted=true
[006] action.end name=set_macro result=ok duration_ms=34
[007] action.start name=apply files=2
[008] input.loaded path=templates.yml sha256=64856a76... bytes=6856
[009] api.result method=configuration.import result=ok path=templates.yml
[010] entity.end type=template_group action=import result=ok name="Templar Templates" id=25
[011] entity.end type=template action=import result=ok name="Test Template" id=10659
...
[037] run.end run_id=20260413T192659Z-1070 result=ok actions=3 created=0 updated=9 failed=0 duration_ms=698
```

Event types:

| Event | When emitted |
|---|---|
| `run.start` | Beginning of every invocation — run ID, target URL, auth method |
| `run.end` | End of every invocation — aggregate counts, total duration |
| `action.start` / `action.end` | Around each top-level action (`set_macro`, `apply`, `decree`, …) with duration |
| `input.loaded` | Each YAML file read — path, SHA-256, byte size |
| `lookup.end` | Bulk existence check before create-or-update decisions |
| `entity.end` | Outcome of each create, update, or import — entity type, name, live ID |
| `api.result` | Outcome of bulk API operations such as `configuration.import` |
| `secret.write` | Token write events — token name and destination, value always redacted |
| `entity.plan` | Pre-flight summary of what an operation intends to change |

Sensitive values are never logged. Macro values appear as `value_redacted=true`, PSK secrets are absent entirely, and API tokens appear as `secret_redacted=true`.

### JSON output

Pass `--json` to any command for newline-delimited JSON, suitable for log aggregation:

```bash
zbxtemplar-exec --json apply deploy.scroll.yml --url ... --token ...
```

Each line is a self-contained JSON object with the same fields as the text format.

## Recommended Operating Model

Use a test Zabbix instance first, then production.

That is the intended safety model for this project:

1. generate artifacts
2. review them
3. validate them in test
4. re-run against production

The executor is designed around idempotent re-apply more than around a separate dry-run engine.

