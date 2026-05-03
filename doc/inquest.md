# Inquest Guide

## Purpose

`zbxtemplar-inquest` compares your declared Zabbix configuration (decree YAML, scrolls, or Zabbix exports) against the live state on a Zabbix server and prints what differs.

It is read-only — no changes are made to Zabbix.

## Installation

`zbxtemplar-inquest` ships with the base install:

```bash
pip install .
```

## Authentication

Same connection inputs as `zbxtemplar-exec`:

- `--url` or `ZABBIX_URL`
- `--token` or `ZABBIX_TOKEN`
- `--user` or `ZABBIX_USER`
- `--password` or `ZABBIX_PASSWORD`

Use `--token` for automation, or `--user` + `--password` for bootstrap.

```bash
zbxtemplar-inquest --url https://zabbix.example.com --token "$ZABBIX_TOKEN" \
  schema decree.yml
```

## Usage

```bash
zbxtemplar-inquest [--url URL] [--token TOKEN] [--user USER] [--password PASSWORD] \
                   {raw,schema} file [file ...]
```

`files` accept any of decree, scroll, or `zabbix_export` YAML — the format is auto-detected.

## Comparison Modes

### `raw`

Reports every field-level difference between the declared YAML and the live API response.

```bash
zbxtemplar-inquest --token "$ZABBIX_TOKEN" raw decree.yml
```

### `schema`

Same comparison, but quietly skips fields that the YAML doesn't set and that Zabbix has filled in with its documented default. Use this mode to focus on real drift; use `raw` when you want to see absolutely everything.

```bash
zbxtemplar-inquest --token "$ZABBIX_TOKEN" schema decree.yml
```

## What Is Compared

`zbxtemplar-inquest` compares the same configuration that `zbxtemplar-exec` applies from decree files:

- user groups
- users
- actions
- host encryption
- SAML directory

Templates and hosts are not compared.

## Output

### Human-readable (default)

A tree grouped by entity, colorized when stdout is a terminal:

```
Checking declared state against zabbix.example.com (schema)
  3 diffs across 2 entities

  DIFF   user_group       Operations
      ~ gui_access:
        local:  "INTERNAL"
        remote: "DEFAULT"
  MISS   action           Notify on disk full
  MISS   user_group       Sales
```

Status tags:

| Tag     | Meaning                                         |
| ------- | ----------------------------------------------- |
| `OK`    | Entity matches                                  |
| `DIFF`  | Entity exists on both sides; some fields differ |
| `MISS`  | Declared locally, not found on remote           |
| `EXTRA` | Present on remote, not declared locally         |

Field markers inside a `DIFF` block:

| Marker  | Meaning                                |
| ------- | -------------------------------------- |
| `+ key` | Field only on remote                   |
| `- key` | Field only on local                    |
| `~ key` | Field present on both, value differs   |

### JSON Lines

Pass `--json` to get one JSON object per diff, suitable for CI pipelines or log aggregation:

```bash
zbxtemplar-inquest --token "$ZABBIX_TOKEN" schema decree.yml --json
```

```json
{"path": "user_group.Operations.gui_access", "local": "INTERNAL", "remote": "DEFAULT"}
```

`path` identifies the entity and field. `local` is `null` when the item exists only on the remote; `remote` is `null` when it exists only locally. Errors are emitted as `{"event": "error", "message": "..."}`.

## Exit Codes

| Code  | Meaning                                                  |
| ----- | -------------------------------------------------------- |
| `0`   | No differences found                                     |
| `1`   | Differences found, or no comparison mode given           |
| `2`   | Error (auth failure, connection error, invalid YAML, …)  |
| `130` | Interrupted by the user                                  |

These map cleanly to CI: treat non-zero as "needs review".

## Typical Use

`zbxtemplar-inquest` reports drift between the declared YAML and an already-deployed Zabbix server. Common uses:

- after an apply, to confirm the live state matches the declaration;
- as a periodic drift check in CI, to catch out-of-band changes made through the Zabbix UI;
- when investigating an incident, to quickly see how the live configuration differs from what is in git.

It is not a dry-run of `zbxtemplar-exec apply`. The diff describes the current gap between declaration and live state, not the exact set of operations a future apply would perform.