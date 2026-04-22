from zbxtemplar.zabbix.trigger_expression import TriggerExpr, TriggerFunction


class Ascii(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("ascii", value)


class Bitlength(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("bitlength", value)


class Bytelength(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("bytelength", value)


class Char(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("char", value)


class Concat(TriggerFunction):
    def __init__(self, *values: TriggerExpr):
        super().__init__("concat", *values)


class Insert(TriggerFunction):
    def __init__(self, value: TriggerExpr, start: int, length: int, replacement: TriggerExpr):
        super().__init__("insert", value, start, length, replacement)


class Jsonpath(TriggerFunction):
    def __init__(self, value: TriggerExpr, path: str, default: str | None = None):
        super().__init__("jsonpath", value, path, default)


class Left(TriggerFunction):
    def __init__(self, value: TriggerExpr, count: int):
        super().__init__("left", value, count)


class Length(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("length", value)


class Ltrim(TriggerFunction):
    def __init__(self, value: TriggerExpr, characters: str | None = None):
        super().__init__("ltrim", value, characters)


class Mid(TriggerFunction):
    def __init__(self, value: TriggerExpr, start: int, count: int):
        super().__init__("mid", value, start, count)


class Repeat(TriggerFunction):
    def __init__(self, value: TriggerExpr, count: int):
        super().__init__("repeat", value, count)


class Replace(TriggerFunction):
    def __init__(self, value: TriggerExpr, pattern: str, replacement: str):
        super().__init__("replace", value, pattern, replacement)


class Right(TriggerFunction):
    def __init__(self, value: TriggerExpr, count: int):
        super().__init__("right", value, count)


class Rtrim(TriggerFunction):
    def __init__(self, value: TriggerExpr, characters: str | None = None):
        super().__init__("rtrim", value, characters)


class Trim(TriggerFunction):
    def __init__(self, value: TriggerExpr, characters: str | None = None):
        super().__init__("trim", value, characters)


class Xmlxpath(TriggerFunction):
    def __init__(self, value: TriggerExpr, path: str, default: str | None = None):
        super().__init__("xmlxpath", value, path, default)