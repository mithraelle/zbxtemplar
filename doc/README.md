# zbxtemplar Documentation

This directory is the structured documentation for `zbxtemplar`.

## What zbxtemplar is

`zbxtemplar` is a Python-based "Monitoring as Code" toolkit for Zabbix:

- `TemplarModule` generates Zabbix-native YAML for templates and hosts.
- `DecreeModule` generates decree YAML for users, user groups, SAML directories, actions, host encryption, and global macros.
- `zbxtemplar-exec` applies those artifacts to a live Zabbix instance.

The project is aimed at teams who want monitoring configuration, access control, SSO provisioning, host security, and alert routing to live in code and git instead of being managed manually in the Zabbix UI.

## Documentation Map

- [Getting Started](./getting-started.md)  
  Installation, first module, and the basic generation workflow.

- [Architecture](./architecture.md)  
  Project structure, core concepts, output formats, and end-to-end flow.

- [Generator Guide](./generator.md)  
  Module loading, CLI flags, context handling, and output behavior.

- [Executor Guide](./executor.md)  
  Authentication, apply/decree/scroll workflows, environment interpolation, and operational guidance.

- [Actions Guide](./actions.md)  
  Trigger/autoregistration actions, condition expressions, and supported operations.

- [Security & Safety](./security.md)  
  Secret management, macro types, host encryption, token safety, fail-fast validation, and the two-stage validation model.

- [Decree Reference](./decree_reference.md)  
  Automatically generated reference for all valid configuration fields.

- [Cheatsheets](./cheatsheet/README.md)  
  Compact authoring references for configuration entities, action rules, and expression builders.

## Recommended Reading Order

1. Start with [Getting Started](./getting-started.md).
2. Read [Architecture](./architecture.md) for the mental model.
3. Use [Generator Guide](./generator.md) and [Executor Guide](./executor.md) as day-to-day reference.
4. Read [Actions Guide](./actions.md) when you need decree-based alerting and routing.
5. Read [Security & Safety](./security.md) for the operational safety model.
