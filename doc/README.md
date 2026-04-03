# zbxtemplar Documentation

This directory is the structured documentation for `zbxtemplar`.

## What zbxtemplar is

`zbxtemplar` is a Python-based "Monitoring as Code" toolkit for Zabbix:

- `TemplarModule` generates Zabbix-native YAML for templates and hosts.
- `DecreeModule` generates decree YAML for users, user groups, and actions.
- `zbxtemplar-exec` applies those artifacts to a live Zabbix instance.

The project is aimed at teams who want monitoring configuration, access control, and alert routing to live in code and git instead of being managed manually in the Zabbix UI.

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

## Recommended Reading Order

1. Start with [Getting Started](./getting-started.md).
2. Read [Architecture](./architecture.md) for the mental model.
3. Use [Generator Guide](./generator.md) and [Executor Guide](./executor.md) as day-to-day reference.
4. Read [Actions Guide](./actions.md) when you need decree-based alerting and routing.
