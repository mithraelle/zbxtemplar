from zbxtemplar.zabbix.trigger_expression import TriggerExpr, TriggerFunction


class Bitand(TriggerFunction):
    """The value of bitwise AND of an item value and mask.

    Zabbix group: Bitwise functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/bitwise
    """
    def __init__(self, value: TriggerExpr, mask: int):
        super().__init__("bitand", value, mask)


class Bitlshift(TriggerFunction):
    """The bitwise shift left of an item value.

    Zabbix group: Bitwise functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/bitwise
    """
    def __init__(self, value: TriggerExpr, bits: int):
        super().__init__("bitlshift", value, bits)


class Bitnot(TriggerFunction):
    """The value of bitwise NOT of an item value.

    Zabbix group: Bitwise functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/bitwise
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("bitnot", value)


class Bitor(TriggerFunction):
    """The value of bitwise OR of an item value and mask.

    Zabbix group: Bitwise functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/bitwise
    """
    def __init__(self, value: TriggerExpr, mask: int):
        super().__init__("bitor", value, mask)


class Bitrshift(TriggerFunction):
    """The bitwise shift right of an item value.

    Zabbix group: Bitwise functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/bitwise
    """
    def __init__(self, value: TriggerExpr, bits: int):
        super().__init__("bitrshift", value, bits)


class Bitxor(TriggerFunction):
    """The value of bitwise exclusive OR of an item value and mask.

    Zabbix group: Bitwise functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/bitwise
    """
    def __init__(self, value: TriggerExpr, mask: int):
        super().__init__("bitxor", value, mask)
