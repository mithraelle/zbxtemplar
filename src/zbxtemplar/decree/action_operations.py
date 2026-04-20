from typing import Self


def _name(value):
    if hasattr(value, 'name'):
        return value.name
    if hasattr(value, 'username'):
        return value.username
    return value


class SendMessageOperation:
    """A single send-message step within an action."""

    operationtype = 0

    def __init__(self, users: list | None = None,
                 groups: list | None = None,
                 media_type=None,
                 subject: str | None = None,
                 message: str | None = None,
                 step_from: int | None = None,
                 step_to: int | None = None,
                 step_duration: int | None = None):
        """
        Args:
            users: User objects or username strings to notify.
            groups: UserGroup objects or group name strings to notify.
            media_type: MediaType constant or name string; None sends via all enabled media.
            subject: Override default message subject template.
            message: Override default message body template.
            step_from: Escalation step range start (TriggerOperations only).
            step_to: Escalation step range end (TriggerOperations only).
            step_duration: Step duration in seconds (TriggerOperations only).
        """
        self.users = [_name(u) for u in (users or [])]
        self.groups = [_name(g) for g in (groups or [])]
        self.media_type = _name(media_type) if media_type is not None else None
        self.subject = subject
        self.message = message
        self.step_from = step_from
        self.step_to = step_to
        self.step_duration = step_duration

    def to_dict(self) -> dict:
        d = {"operationtype": self.operationtype}
        opmessage = {}
        if self.media_type is not None:
            opmessage["mediatypeid"] = self.media_type
        if self.subject is not None or self.message is not None:
            opmessage["default_msg"] = 0
            if self.subject is not None:
                opmessage["subject"] = self.subject
            if self.message is not None:
                opmessage["message"] = self.message
        if opmessage:
            d["opmessage"] = opmessage
        if self.users:
            d["opmessage_usr"] = [{"userid": u} for u in self.users]
        if self.groups:
            d["opmessage_grp"] = [{"usrgrpid": g} for g in self.groups]
        if self.step_from is not None:
            d["esc_step_from"] = self.step_from
        if self.step_to is not None:
            d["esc_step_to"] = self.step_to
        if self.step_duration is not None:
            d["esc_period"] = self.step_duration
        return d

    @classmethod
    def from_dict(cls, data: dict):
        opmessage = data.get("opmessage", {})
        users = [u.get("userid") for u in data.get("opmessage_usr", [])]
        groups = [g.get("usrgrpid") for g in data.get("opmessage_grp", [])]
        return cls(
            users=users,
            groups=groups,
            media_type=opmessage.get("mediatypeid"),
            subject=opmessage.get("subject"),
            message=opmessage.get("message"),
            step_from=data.get("esc_step_from"),
            step_to=data.get("esc_step_to"),
            step_duration=data.get("esc_period"),
        )



class TriggerOperations:
    """Problem escalation notification steps for TriggerAction.operations."""

    def __init__(self):
        self._ops: list[SendMessageOperation] = []

    def send_message(self, users: list | None = None,
                     groups: list | None = None,
                     media_type=None,
                     subject: str | None = None,
                     message: str | None = None,
                     step_from: int = 1, step_to: int = 1,
                     step_duration: int = 0) -> Self:
        """Append a send-message escalation step. Returns self for chaining."""
        self._ops.append(SendMessageOperation(
            users=users, groups=groups,
            media_type=media_type, subject=subject,
            message=message,
            step_from=step_from, step_to=step_to,
            step_duration=step_duration,
        ))
        return self

    def to_list(self) -> list:
        return [op.to_dict() for op in self._ops]

    @classmethod
    def from_dict(cls, data: list):
        obj = cls()
        for d in data:
            if d.get("operationtype") == SendMessageOperation.operationtype:
                obj._ops.append(SendMessageOperation.from_dict(d))
        return obj


class AddHostOperation:
    operationtype = 2

    def to_dict(self) -> dict:
        return {"operationtype": self.operationtype}

    @classmethod
    def from_dict(cls, data: dict):
        return cls()


class AddToGroupOperation:
    operationtype = 4

    def __init__(self, group):
        self.group = _name(group)

    def to_dict(self) -> dict:
        return {
            "operationtype": self.operationtype,
            "opgroup": [{"groupid": self.group}],
        }

    @classmethod
    def from_dict(cls, data: dict):
        group = data.get("opgroup", [{}])[0].get("groupid")
        return cls(group)


class LinkTemplateOperation:
    operationtype = 6

    def __init__(self, template):
        self.template = _name(template)

    def to_dict(self) -> dict:
        return {
            "operationtype": self.operationtype,
            "optemplate": [{"templateid": self.template}],
        }

    @classmethod
    def from_dict(cls, data: dict):
        template = data.get("optemplate", [{}])[0].get("templateid")
        return cls(template)


class EnableHostOperation:
    operationtype = 8

    def to_dict(self) -> dict:
        return {"operationtype": self.operationtype}

    @classmethod
    def from_dict(cls, data: dict):
        return cls()


class DisableHostOperation:
    operationtype = 9

    def to_dict(self) -> dict:
        return {"operationtype": self.operationtype}

    @classmethod
    def from_dict(cls, data: dict):
        return cls()


class SetInventoryModeOperation:
    operationtype = 10

    MANUAL = 0
    AUTOMATIC = 1

    def __init__(self, inventory_mode: int = MANUAL):
        self.inventory_mode = inventory_mode

    def to_dict(self) -> dict:
        return {
            "operationtype": self.operationtype,
            "opinventory": {"inventory_mode": self.inventory_mode},
        }

    @classmethod
    def from_dict(cls, data: dict):
        mode = data.get("opinventory", {}).get("inventory_mode", cls.MANUAL)
        return cls(mode)


class AutoregistrationOperations:
    """Host provisioning and notification steps for AutoregistrationAction.operations."""

    def __init__(self):
        self._ops: list = []

    def send_message(self, users: list | None = None,
                     groups: list | None = None,
                     media_type=None,
                     subject: str | None = None,
                     message: str | None = None) -> Self:
        """Append a send-message step. Returns self for chaining."""
        self._ops.append(SendMessageOperation(
            users=users, groups=groups,
            media_type=media_type, subject=subject,
            message=message,
        ))
        return self

    def add_host(self) -> Self:
        """Register the newly discovered host in Zabbix."""
        self._ops.append(AddHostOperation())
        return self

    def add_to_group(self, group) -> Self:
        """Add host to a host group. Accepts HostGroup object or name string."""
        self._ops.append(AddToGroupOperation(group))
        return self

    def link_template(self, template) -> Self:
        """Link a template to the host. Accepts Template object or name string."""
        self._ops.append(LinkTemplateOperation(template))
        return self

    def enable_host(self) -> Self:
        """Set the host status to enabled."""
        self._ops.append(EnableHostOperation())
        return self

    def disable_host(self) -> Self:
        """Set the host status to disabled."""
        self._ops.append(DisableHostOperation())
        return self

    def set_inventory_mode(self, mode: int = SetInventoryModeOperation.MANUAL) -> Self:
        """Set host inventory collection mode: MANUAL (0) or AUTOMATIC (1)."""
        self._ops.append(SetInventoryModeOperation(mode))
        return self

    def to_list(self) -> list:
        return [op.to_dict() for op in self._ops]

    @classmethod
    def from_dict(cls, data: list):
        obj = cls()
        mapping = {
            0: SendMessageOperation,
            2: AddHostOperation,
            4: AddToGroupOperation,
            6: LinkTemplateOperation,
            8: EnableHostOperation,
            9: DisableHostOperation,
            10: SetInventoryModeOperation,
        }
        for d in data:
            op_cls = mapping.get(d.get("operationtype"))
            if op_cls:
                obj._ops.append(op_cls.from_dict(d))
        return obj


class TriggerAckOperations:
    """Notification steps for recovery and acknowledgment events in TriggerAction."""

    def __init__(self):
        self._ops: list[SendMessageOperation] = []

    def send_message(self, users: list | None = None,
                     groups: list | None = None,
                     media_type=None,
                     subject: str | None = None,
                     message: str | None = None) -> Self:
        """Append a send-message step. Returns self for chaining."""
        self._ops.append(SendMessageOperation(
            users=users, groups=groups,
            media_type=media_type, subject=subject,
            message=message,
        ))
        return self

    def to_list(self) -> list:
        return [op.to_dict() for op in self._ops]

    @classmethod
    def from_dict(cls, data: list):
        obj = cls()
        for d in data:
            if d.get("operationtype") == SendMessageOperation.operationtype:
                obj._ops.append(SendMessageOperation.from_dict(d))
        return obj