# Decree Configuration Reference

> This document is automatically generated from the Python source code.
> Any edits or new parameters should be added directly to the `_SCHEMA` definitions in Python.

---

## Scroll
Ordered deployment scroll: bootstrap, global macros, imports, and decree.

* `set_super_admin` (Optional, *SuperAdmin*): Super admin update — password and/or username. Requires current_password when changing password.
* `set_macro` (Optional, *list[Macro]*): Global macro definition, list of definitions, or path to a macro YAML file.
* `apply` (Optional, *str | list[str]*): Zabbix-native YAML file path or paths to import.
* `decree` (Optional, *Decree*): Inline decree data, merged decree data list, or decree YAML path.

## Decree
Decree YAML contents: user groups, users, actions, and host encryption.

* `user_group` (Optional, *list[UserGroup]*): User group definitions to create or update before users.
* `add_user` (Optional, *list[User]*): User definitions to create or update.
* `actions` (Optional, *list[dict]*): Zabbix action definitions to create or update.
* `encryption` (Optional, *list[EncryptionDecree]*): Host encryption settings with host_defaults and hosts entries.

## SuperAdmin
Super admin credentials update for the authenticated user.

* `username` (Optional, *str*): New login name for the super admin.
* `password` (Optional, *str*): New password.
* `current_password` (Optional, *str*): Current password (required when changing password).

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
* `connect` (Optional, *str*): Comma-separated encryption modes used for outbound connections: UNENCRYPTED, PSK, or CERT.
* `accept` (Optional, *str*): Comma-separated encryption modes accepted by the host: UNENCRYPTED, PSK, or CERT.
* `psk_identity` (Optional, *str*): PSK identity required when PSK mode is enabled.
* `psk` (Optional, *str*): PSK secret required when PSK mode is enabled.
* `issuer` (Optional, *str*): TLS certificate issuer required with subject when CERT mode is enabled.
* `subject` (Optional, *str*): TLS certificate subject required with issuer when CERT mode is enabled.

## Encryption
Zabbix host-communication encryption settings: modes plus PSK/CERT credentials.

* `connect` (Optional, *str*): Comma-separated encryption modes used for outbound connections: UNENCRYPTED, PSK, or CERT.
* `accept` (Optional, *str*): Comma-separated encryption modes accepted by the host: UNENCRYPTED, PSK, or CERT.
* `psk_identity` (Optional, *str*): PSK identity required when PSK mode is enabled.
* `psk` (Optional, *str*): PSK secret required when PSK mode is enabled.
* `issuer` (Optional, *str*): TLS certificate issuer required with subject when CERT mode is enabled.
* `subject` (Optional, *str*): TLS certificate subject required with issuer when CERT mode is enabled.

## EncryptionDecree
Host encryption block: shared host_defaults plus per-host entries.

* `host_defaults` (Optional, *Encryption*): Default encryption settings merged into each host entry.
* `hosts` (**Required**, *list[HostEncryption]*): Per-host encryption settings to apply.

## Macro
Macro(name: str, value: str, description: str | None = None, type: zbxtemplar.zabbix.macro.MacroType = <MacroType.TEXT: 'TEXT'>)

* `name` (**Required**, *str*): Macro name without {$...} braces.
* `value` (**Required**, *str*): Macro value.
* `description` (Optional, *str*): Optional macro description.
* `type` (Optional, *MacroType*): Macro type: TEXT, SECRET_TEXT, SECRET, or VAULT.
