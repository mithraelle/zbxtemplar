from zbxtemplar.zabbix.trigger_expression import TriggerExpr, TriggerFunction


class Between(TriggerFunction):
    def __init__(self, value: TriggerExpr, min: TriggerExpr, max: TriggerExpr):
        super().__init__("between", value, min, max)


class In(TriggerFunction):
    def __init__(self, value: TriggerExpr, *values: TriggerExpr):
        super().__init__("in", value, *values)