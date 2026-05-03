# zbxtemplar Documentation

This directory is the structured documentation for `zbxtemplar`.

## What zbxtemplar is

`zbxtemplar` is a Python-based "Monitoring as Code" toolkit for Zabbix:

- `TemplarModule` generates Zabbix-native YAML for templates and hosts.
- `DecreeModule` generates decree YAML for users, user groups, SAML directories, actions, host encryption, and global macros.
- `zbxtemplar-exec` applies those artifacts to a live Zabbix instance.
- `zbxtemplar-inquest` compares declared YAML against live Zabbix state (read-only).

The project is aimed at teams who want monitoring configuration, access control, SSO provisioning, host security, and alert routing to live in code and git instead of being managed manually in the Zabbix UI.

## Documentation Map

### Getting oriented

- [Getting Started](./getting-started.md)  
  Installation, first module, and the basic generation workflow.

- [Architecture](./architecture.md)  
  Project structure, core concepts, output formats, and end-to-end flow.

### Authoring (what you write inside `compose()`)

- [Authoring Monitoring](./authoring-monitoring.md)  
  Templates, hosts, items, triggers, the trigger-expression builder, inventory.

- [Authoring Decree](./authoring-decree.md)  
  User groups, users, media, API tokens, SAML JIT provisioning, host encryption, module-level macros.

- [Authoring Actions](./authoring-actions.md)  
  Trigger/autoregistration actions, condition expression trees, supported operations.

### Operating the tool

- [CLI Reference](./cli-reference.md)  
  Module loading, CLI flags, `--param`, `--context`, macro resolution, programmatic loading.

- [Executor Guide](./executor.md)  
  Authentication, apply/decree/scroll workflows, environment interpolation, and operational guidance.

- [Inquest Guide](./inquest.md)  
  Compare declared YAML against live Zabbix state — read-only diff for review and drift checks.

- [Security & Safety](./security.md)  
  Secret management, macro types, host encryption, token safety, fail-fast validation, and the two-stage validation model.

### Reference

- [Decree Reference](./decree_reference.md)  
  Automatically generated reference for all valid configuration fields.

- [Reference](./reference/README.md)  
  Compact, task-oriented lookup tables. The authoring docs above are the narrative companion.
