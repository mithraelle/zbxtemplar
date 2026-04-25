from abc import ABC

from zbxtemplar.decree.DecreeEntity import DecreeEntity
from zbxtemplar.decree.action_conditions import ConditionList, ConditionExpression, ConditionExpr
from zbxtemplar.decree.action_operations import TriggerOperations, TriggerAckOperations, AutoregistrationOperations


# Shared API translation tables — used by both push (executor) and pull (APIContext).
# Direction differs (name↔id) but the shape is identical.

# conditiontype -> (api_name, id_field, label)
CONDITION_RESOLVERS = {
    0:  ("hostgroup", "groupid",    "Host group"),
    1:  ("host",      "hostid",     "Host"),
    2:  ("trigger",   "triggerid",  "Trigger"),
    13: ("template",  "templateid", "Template"),
    18: ("drule",     "druleid",    "Discovery rule"),
    20: ("proxy",     "proxyid",    "Proxy"),
}

# Operation sub-arrays carrying ID-shaped values.
# (parent_key, id_field, api_name, name_field, label)
OP_LIST_TARGETS = [
    ("opmessage_grp", "usrgrpid",   "usergroup", "name",     "User group"),
    ("opmessage_usr", "userid",     "user",      "username", "User"),
    ("opgroup",       "groupid",    "hostgroup", "name",     "Host group"),
    ("optemplate",    "templateid", "template",  "name",     "Template"),
]

# Operation single-field ID translations (parent dict carries the ID directly).
# (parent_key, id_field, api_name, name_field, label)
OP_DICT_TARGETS = [
    ("opmessage", "mediatypeid", "mediatype", "name", "Media type"),
]


class Action(DecreeEntity, ABC):
    """Abstract base for Zabbix actions. Use TriggerAction or AutoregistrationAction."""

    _OMIT_FROM_SCHEMA_DOCS = True
    eventsource = None

    def __init__(self, name: str):
        self.name = name
        self._filter = None

    def set_conditions(self, conditions: ConditionList | ConditionExpression | ConditionExpr):
        """Set the action filter condition.

        Accepts a ConditionList, ConditionExpression, or a bare ConditionExpr tree
        built with ``&`` (and), ``|`` (or), ``~`` (not) operators. Bare trees are
        auto-wrapped into a ConditionExpression.
        """
        if isinstance(conditions, ConditionExpr):
            conditions = ConditionExpression(conditions)
        self._filter = conditions
        return self

    def to_dict(self) -> dict:
        result = {"eventsource": self.eventsource}
        result.update(super().to_dict())
        if self._filter is not None:
            result["filter"] = self._filter.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict):
        eventsource = data.get("eventsource", 0)
        if eventsource == 0:
            return TriggerAction.from_dict(data)
        elif eventsource == 2:
            return AutoregistrationAction.from_dict(data)
        raise ValueError(f"Unknown eventsource '{eventsource}'")


class TriggerAction(Action):
    """Zabbix action for trigger events.

    Configure notifications via:

    - ``.operations`` (TriggerOperations) — problem escalation steps
    - ``.recovery_operations`` (TriggerAckOperations) — recovery notifications
    - ``.update_operations`` (TriggerAckOperations) — acknowledgment notifications
    """

    _OMIT_FROM_SCHEMA_DOCS = True
    eventsource = 0

    def __init__(self, name: str):
        super().__init__(name)
        self.operations = TriggerOperations()
        self.recovery_operations = TriggerAckOperations()
        self.update_operations = TriggerAckOperations()

    def set_operation_step(self, duration: int):
        """Set the escalation step duration in seconds."""
        self.esc_period = duration
        return self

    def pause_symptoms(self):
        """Suppress notifications for symptom (non-root-cause) problems."""
        self.pause_symptoms = 0
        return self

    def pause_suppressed(self):
        """Suppress notifications while the problem is in a maintenance window."""
        self.pause_suppressed = 0
        return self

    def notify_if_canceled(self):
        """Send a notification when the action is canceled."""
        self.notify_if_canceled = 0
        return self

    def operations_to_list(self) -> list:
        return self.operations.to_list()

    def recovery_operations_to_list(self) -> list:
        return self.recovery_operations.to_list()

    def update_operations_to_list(self) -> list:
        return self.update_operations.to_list()

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls(data["name"])
        if "esc_period" in data:
            obj.set_operation_step(data["esc_period"])
        if "pause_symptoms" in data:
            obj.pause_symptoms()
        if "pause_suppressed" in data:
            obj.pause_suppressed()
        if "notify_if_canceled" in data:
            obj.notify_if_canceled()
            
        if "filter" in data:
            f = data["filter"]
            if f.get("evaltype") == 3:
                obj.set_conditions(ConditionExpression.from_dict(f))
            else:
                obj.set_conditions(ConditionList.from_dict(f))
                
        if "operations" in data:
            obj.operations = TriggerOperations.from_dict(data["operations"])
        if "recovery_operations" in data:
            obj.recovery_operations = TriggerAckOperations.from_dict(data["recovery_operations"])
        if "update_operations" in data:
            obj.update_operations = TriggerAckOperations.from_dict(data["update_operations"])
        return obj


class AutoregistrationAction(Action):
    """Zabbix action for active agent autoregistration events.

    Configure host provisioning steps via ``.operations`` (AutoregistrationOperations).
    """

    _OMIT_FROM_SCHEMA_DOCS = True
    eventsource = 2

    def __init__(self, name: str):
        super().__init__(name)
        self.operations = AutoregistrationOperations()

    def operations_to_list(self) -> list:
        return self.operations.to_list()

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls(data["name"])
        if "filter" in data:
            f = data["filter"]
            if f.get("evaltype") == 3:
                obj.set_conditions(ConditionExpression.from_dict(f))
            else:
                obj.set_conditions(ConditionList.from_dict(f))
                
        if "operations" in data:
            obj.operations = AutoregistrationOperations.from_dict(data["operations"])
        return obj