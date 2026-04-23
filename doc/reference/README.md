# zbxtemplar Reference

Compact, task-oriented lookup tables for writing zbxtemplar modules — the quick-reference companion to the narrative authoring docs:

- [Authoring Monitoring](../authoring-monitoring.md)
- [Authoring Decree](../authoring-decree.md)
- [Authoring Actions](../authoring-actions.md)

Version-dependent vocabularies (trigger functions, inventory fields, media type and user role names) are imported from `zbxtemplar.catalog.zabbix_7_4`. Only Zabbix 7.4 is currently supported; upgrading is a one-line import change when a newer catalog ships.

| File | Covers |
|---|---|
| `modules.md` | Understand module structure, CLI flags, `--param`, `--context` |
| `templates_hosts.md` | Create templates, hosts, groups, macros, value maps |
| `items_triggers.md` | Add items and triggers to a template or host |
| `trigger_functions_glossary.md` | Look up trigger function wrappers for the expression builder |
| `graphs.md` | Add classic (template-level) graphs |
| `dashboards.md` | Add dashboards and widgets (ClassicGraph, SimpleGraph, ItemHistory, SVG graph) |
| `decree.md` | Define user groups, users, media, API tokens |
| `actions.md` | Configure trigger/autoregistration actions, conditions, operations |
| `saml_encryption.md` | Configure SAML provisioning or host PSK/cert encryption |
