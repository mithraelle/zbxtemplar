from zbxtemplar.zabbix.trigger_expression import TriggerExpr, TriggerFunction


class Between(TriggerFunction):
    """Check if the value belongs to the given range.

    Zabbix group: Operator functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/operator
    """
    def __init__(self, value: TriggerExpr, min: TriggerExpr, max: TriggerExpr):
        super().__init__("between", value, min, max)


class In(TriggerFunction):
    """Check if the value is equal to at least one of the listed values.

    Zabbix group: Operator functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/operator
    """
    def __init__(self, value: TriggerExpr, *values: TriggerExpr):
        super().__init__("in", value, *values)
