from typing import List, Optional


def _name(value):
    if hasattr(value, 'name'):
        return value.name
    if hasattr(value, 'username'):
        return value.username
    return value


class SendMessageOperation:
    operationtype = 0

    def __init__(self, users: Optional[List] = None,
                 groups: Optional[List] = None,
                 media_type=None,
                 subject: Optional[str] = None,
                 message: Optional[str] = None,
                 step_from: Optional[int] = None,
                 step_to: Optional[int] = None,
                 step_duration: Optional[int] = None):
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


class TriggerOperations:
    def __init__(self):
        self._ops: List[SendMessageOperation] = []

    def send_message(self, users: Optional[List] = None,
                     groups: Optional[List] = None,
                     media_type=None,
                     subject: Optional[str] = None,
                     message: Optional[str] = None,
                     step_from: int = 1, step_to: int = 1,
                     step_duration: int = 0) -> 'TriggerOperations':
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


class AddHostOperation:
    operationtype = 2

    def to_dict(self) -> dict:
        return {"operationtype": self.operationtype}


class AddToGroupOperation:
    operationtype = 4

    def __init__(self, group):
        self.group = _name(group)

    def to_dict(self) -> dict:
        return {
            "operationtype": self.operationtype,
            "opgroup": [{"groupid": self.group}],
        }


class LinkTemplateOperation:
    operationtype = 6

    def __init__(self, template):
        self.template = _name(template)

    def to_dict(self) -> dict:
        return {
            "operationtype": self.operationtype,
            "optemplate": [{"templateid": self.template}],
        }


class EnableHostOperation:
    operationtype = 8

    def to_dict(self) -> dict:
        return {"operationtype": self.operationtype}


class DisableHostOperation:
    operationtype = 9

    def to_dict(self) -> dict:
        return {"operationtype": self.operationtype}


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


class AutoregistrationOperations:
    def __init__(self):
        self._ops: List = []

    def send_message(self, users: Optional[List] = None,
                     groups: Optional[List] = None,
                     media_type=None,
                     subject: Optional[str] = None,
                     message: Optional[str] = None) -> 'AutoregistrationOperations':
        self._ops.append(SendMessageOperation(
            users=users, groups=groups,
            media_type=media_type, subject=subject,
            message=message,
        ))
        return self

    def add_host(self) -> 'AutoregistrationOperations':
        self._ops.append(AddHostOperation())
        return self

    def add_to_group(self, group) -> 'AutoregistrationOperations':
        self._ops.append(AddToGroupOperation(group))
        return self

    def link_template(self, template) -> 'AutoregistrationOperations':
        self._ops.append(LinkTemplateOperation(template))
        return self

    def enable_host(self) -> 'AutoregistrationOperations':
        self._ops.append(EnableHostOperation())
        return self

    def disable_host(self) -> 'AutoregistrationOperations':
        self._ops.append(DisableHostOperation())
        return self

    def set_inventory_mode(self, mode: int = SetInventoryModeOperation.MANUAL) -> 'AutoregistrationOperations':
        self._ops.append(SetInventoryModeOperation(mode))
        return self

    def to_list(self) -> list:
        return [op.to_dict() for op in self._ops]


class TriggerAckOperations:
    def __init__(self):
        self._ops: List[SendMessageOperation] = []

    def send_message(self, users: Optional[List] = None,
                     groups: Optional[List] = None,
                     media_type=None,
                     subject: Optional[str] = None,
                     message: Optional[str] = None) -> 'TriggerAckOperations':
        self._ops.append(SendMessageOperation(
            users=users, groups=groups,
            media_type=media_type, subject=subject,
            message=message,
        ))
        return self

    def to_list(self) -> list:
        return [op.to_dict() for op in self._ops]