from zbxtemplar.zabbix.trigger_expression import TriggerExpr, TriggerFunction


class Bitand(TriggerFunction):
    def __init__(self, value: TriggerExpr, mask: int):
        super().__init__("bitand", value, mask)


class Bitlshift(TriggerFunction):
    def __init__(self, value: TriggerExpr, bits: int):
        super().__init__("bitlshift", value, bits)


class Bitnot(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("bitnot", value)


class Bitor(TriggerFunction):
    def __init__(self, value: TriggerExpr, mask: int):
        super().__init__("bitor", value, mask)


class Bitrshift(TriggerFunction):
    def __init__(self, value: TriggerExpr, bits: int):
        super().__init__("bitrshift", value, bits)


class Bitxor(TriggerFunction):
    def __init__(self, value: TriggerExpr, mask: int):
        super().__init__("bitxor", value, mask)