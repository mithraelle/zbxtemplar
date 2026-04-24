# Decree — Users, Groups, Media, Tokens

`self.*` calls below are `DecreeModule` methods called from inside `compose()`.

## Imports

```python
from zbxtemplar.modules import DecreeModule
from zbxtemplar.decree import (
    GuiAccess, UsersStatus, Permission,
    Severity, Token,
)
from zbxtemplar.catalog.zabbix_7_4 import MediaType, UserRole
```

## User groups

```python
group = self.add_user_group(
    "Ops Team",
    gui_access=GuiAccess.INTERNAL,    # DEFAULT, INTERNAL, LDAP, DISABLED
    users_status=UsersStatus.ENABLED, # ENABLED, DISABLED
)
```

### Permissions

```python
# accepts name string or HostGroup / TemplateGroup object
group.link_host_group("Linux servers", Permission.READ)
group.link_host_group(self.context.get_host_group("Prod"), Permission.READ_WRITE)
group.link_template_group("My Templates", Permission.READ)
# Permission: NONE, READ, READ_WRITE
```

## Users

```python
user = self.add_user("alice", role=UserRole.ADMIN)
# UserRole: SUPER_ADMIN, ADMIN, USER, GUEST

user.set_password("${ENV_VAR}")   # ${VAR} syntax pulls value from environment at executor time
user.link_group(group)
```

### Media

```python
media = user.add_media(MediaType.EMAIL, "alice@example.com")
media.set_severity([Severity.HIGH, Severity.DISASTER])
# Severity: NOT_CLASSIFIED, INFORMATION, WARNING, AVERAGE, HIGH, DISASTER
media.set_period("1-7,00:00-24:00")   # Zabbix time period string; default: all hours

user.add_media(MediaType.SLACK, "#alerts")
```

Common `MediaType` constants: EMAIL, SLACK, TELEGRAM, MS_TEAMS, MS_TEAMS_WORKFLOW,
PAGERDUTY, OPSGENIE, DISCORD, SMS, MATTERMOST, ROCKET_CHAT, PUSHOVER, VICTOROPS.
Full list in `zbxtemplar.catalog.zabbix_7_4.MediaType`.

### API tokens

```python
user.set_token(
    "token-name",
    store_at=".secrets/token.txt",
    expires_at=Token.EXPIRES_NEVER,
    force=True,   # revoke and recreate if token already exists
)
# store_at=Token.STDOUT — print token value to stdout instead of writing a file
# expires_at: Token.EXPIRES_NEVER or a future unix timestamp (int)
```