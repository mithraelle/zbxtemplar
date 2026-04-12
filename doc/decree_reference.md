# Decree Configuration Reference

> This document is automatically generated from the Python source code (`DictEntity` schemas).
> Any edits or new parameters should be added directly to the `_SCHEMA` definitions in Python.

---

## ScrollExecutor
Executor for ordered scroll actions that combine bootstrap, import, and decree steps.

* `set_super_admin` (Optional, *str | dict*): New built-in Admin password as a string or password mapping.
* `set_macro` (Optional, *str | dict | list*): Global macro definition, list of definitions, or path to a macro YAML file.
* `apply` (Optional, *str | list[str]*): Zabbix-native YAML file path or paths to import.
* `decree` (Optional, *dict | list | str*): Inline decree data, merged decree data list, or decree YAML path.

## DecreeExecutor
Executor for decree YAML sections such as user groups, users, actions, and encryption.

* `user_group` (Optional, *list[UserGroup]*): User group definitions to create or update before users.
* `add_user` (Optional, *list[User]*): User definitions to create or update.
* `actions` (Optional, *list[dict]*): Zabbix action definitions to create or update.
* `encryption` (Optional, *dict | list[dict]*): Host encryption settings with host_defaults and hosts entries.

## UserMedia
Notification media configuration for a managed user.

* `type` (**Required**, *str*): Zabbix media type name.
* `sendto` (**Required**, *str*): Recipient address or target for the media type.
* `severity` (Optional, *list[str] | str*): Enabled trigger severities as a list or comma-separated string.
* `period` (Optional, *str*): Zabbix media active time period, for example 1-7,00:00-24:00.

## UserGroup
Zabbix user group and permission mapping managed by decree YAML.

* `name` (**Required**, *str*): Zabbix user group name.
* `gui_access` (Optional, *str*): GUI access mode: DEFAULT, INTERNAL, LDAP, or DISABLED.
* `host_groups` (Optional, *list[dict]*): Host group permission entries with name and permission.
* `template_groups` (Optional, *list[dict]*): Template group permission entries with name and permission.

## User
Zabbix user account managed by decree YAML.

* `username` (**Required**, *str*): Zabbix username.
* `role` (**Required**, *str*): Zabbix role name assigned to the user.
* `password` (Optional, *str*): Password to set when creating or updating the user.
* `groups` (Optional, *list[str]*): User group names to attach to the user.
* `medias` (Optional, *list[UserMedia]*): Media definitions for the user.
* `token` (Optional, *Token*): API token provisioning configuration for the user.
* `force_token` (Optional, *bool*): Update and re-generate an existing token with the same name.

## Token
API token provisioning settings for a managed user.

* `name` (**Required**, *str*): API token name.
* `store_at` (**Required**, *str*): Output sink for the generated token secret: a file path or STDOUT.
* `expires_at` (Optional, *int | NEVER*): Token expiration as a future Unix timestamp, or NEVER for a non-expiring token.

## HostEncryption
Host-level encryption settings applied through the Zabbix API.

* `host` (**Required**, *str*): Zabbix host technical name to update.
* `connect` (**Required**, *str*): Comma-separated encryption modes used for outbound connections: UNENCRYPTED, PSK, or CERT.
* `accept` (**Required**, *str*): Comma-separated encryption modes accepted by the host: UNENCRYPTED, PSK, or CERT.
* `psk_identity` (Optional, *str*): PSK identity required when PSK mode is enabled.
* `psk` (Optional, *str*): PSK secret required when PSK mode is enabled.
* `issuer` (Optional, *str*): TLS certificate issuer required with subject when CERT mode is enabled.
* `subject` (Optional, *str*): TLS certificate subject required with issuer when CERT mode is enabled.
