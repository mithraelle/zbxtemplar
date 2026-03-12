from typing import List, Optional


class SendMessageOperation:
    operationtype = 0

    def __init__(self, users: Optional[List[str]] = None,
                 groups: Optional[List[str]] = None,
                 media_type: Optional[str] = None,
                 subject: Optional[str] = None,
                 message: Optional[str] = None,
                 step_from: Optional[int] = None,
                 step_to: Optional[int] = None,
                 step_duration: Optional[int] = None):
        self.users = users or []
        self.groups = groups or []
        self.media_type = media_type
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

    def send_message(self, users: Optional[List[str]] = None,
                     groups: Optional[List[str]] = None,
                     media_type: Optional[str] = None,
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


class TriggerAckOperations:
    def __init__(self):
        self._ops: List[SendMessageOperation] = []

    def send_message(self, users: Optional[List[str]] = None,
                     groups: Optional[List[str]] = None,
                     media_type: Optional[str] = None,
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