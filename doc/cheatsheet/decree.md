# Decree — Users & Groups

`self.*` calls below are `DecreeModule` methods called from inside `compose()`.

## Imports

```python
from zbxtemplar.modules import DecreeModule
from zbxtemplar.decree import (
    GuiAccess, UsersStatus, Permission,
    MediaType, UserRole, Severity,
    UserMedia, Token,
)
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
group.add_host_group("Linux servers", Permission.READ)
group.add_host_group(self.context.get_host_group("Prod"), Permission.READ_WRITE)
group.add_template_group("My Templates", Permission.READ)
# Permission: NONE, READ, READ_WRITE
```

## Users

```python
user = self.add_user("alice", role=UserRole.ADMIN)
# UserRole: SUPER_ADMIN, ADMIN, USER, GUEST

user.set_password("${ENV_VAR}")   # ${VAR} syntax pulls value from environment at executor time
user.add_group(group)
```

### Media

```python
media = UserMedia(MediaType.EMAIL, "alice@example.com")
media.set_severity([Severity.HIGH, Severity.DISASTER])
# Severity: NOT_CLASSIFIED, INFORMATION, WARNING, AVERAGE, HIGH, DISASTER
media.set_period("1-7,00:00-24:00")   # Zabbix time period string; default: all hours

user.add_media(media)
user.add_media(UserMedia(MediaType.SLACK, "#alerts"))
```

Common `MediaType` constants: EMAIL, SLACK, TELEGRAM, MS_TEAMS, MS_TEAMS_WORKFLOW,
PAGERDUTY, OPSGENIE, DISCORD, SMS, MATTERMOST, ROCKET_CHAT, PUSHOVER, VICTOROPS.
Full list in `zbxtemplar.decree.DecreeEntity.MediaType`.

### API tokens

```python
user.set_token(
    Token("token-name", store_at=".secrets/token.txt", expires_at=Token.NEVER),
    force=True,   # revoke and recreate if token already exists
)
# store_at=Token.STDOUT — print token value to stdout instead of writing a file
# expires_at: Token.NEVER or a future unix timestamp (int)
```