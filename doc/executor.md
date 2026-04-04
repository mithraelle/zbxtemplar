# Executor Guide

## Purpose

`zbxtemplar-exec` applies generated artifacts to a live Zabbix instance.

It handles two broad cases:

- importing Zabbix-native YAML
- applying decree YAML for stateful objects such as users, groups, and actions

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

```bash
zbxtemplar-exec decree decree.yml --url ... --token ...
```

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
- `force_token: true` generates a new secret for an existing token and ensures it is enabled
- duplicate `store_at` paths in one run are rejected
- writing to an already existing output file is rejected

### `set_macro`

Sets global macros inline or from a file.

```bash
zbxtemplar-exec set_macro SNMP_COMMUNITY public --url ... --token ...
zbxtemplar-exec set_macro macros.yml --url ... --token ...
```

### `set_super_admin`

Updates the built-in super admin password:

```bash
zbxtemplar-exec set_super_admin --new-password "$ZBX_ADMIN_PASSWORD" --url ... --password ...
```

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

Sensitive string values may contain `${VAR_NAME}` placeholders.

Before mutating operations run, the executor performs a pre-flight scan. If any required environment variable is missing, execution aborts before touching the API.

This applies to data-oriented commands such as:

- `set_super_admin`
- `set_macro`
- decree user handling
- scroll inputs that feed those actions

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

These are worth knowing before relying on the executor heavily:

- Executor API calls are not yet wrapped in structured error handling, so environmental failures can still surface as raw tracebacks.
- `force_token` is an aggressive token rotation that overwrites the existing secret, not a graceful coordinated rotation.
- Unknown YAML keys are not yet warned on consistently across all input paths.
- Partial progress logging could be clearer during long or multi-step applies.

Those items are tracked in [Project Status](./project-status.md).
