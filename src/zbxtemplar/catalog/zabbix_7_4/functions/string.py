from zbxtemplar.zabbix.trigger_expression import TriggerExpr, TriggerFunction


class Ascii(TriggerFunction):
    """The ASCII code of the leftmost character of the value.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("ascii", value)


class Bitlength(TriggerFunction):
    """The length of value in bits.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("bitlength", value)


class Bytelength(TriggerFunction):
    """The length of value in bytes.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("bytelength", value)


class Char(TriggerFunction):
    """Return the character by interpreting the value as ASCII code.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("char", value)


class Concat(TriggerFunction):
    """The string resulting from concatenating the referenced item values or constant values.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, *values: TriggerExpr):
        super().__init__("concat", *values)


class Insert(TriggerFunction):
    """Insert specified characters or spaces into the character string beginning at the
    specified position in the string.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, start: int, length: int, replacement: TriggerExpr):
        super().__init__("insert", value, start, length, replacement)


class Jsonpath(TriggerFunction):
    """Return the JSONPath result.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, path: str, default: str | None = None):
        super().__init__("jsonpath", value, path, default)


class Left(TriggerFunction):
    """Return the leftmost characters of the value.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, count: int):
        super().__init__("left", value, count)


class Length(TriggerFunction):
    """The length of value in characters.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("length", value)


class Ltrim(TriggerFunction):
    """Remove specified characters from the beginning of string.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, characters: str | None = None):
        super().__init__("ltrim", value, characters)


class Mid(TriggerFunction):
    """Return a substring of N characters beginning at the character position specified by
    'start'.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, start: int, count: int):
        super().__init__("mid", value, start, count)


class Repeat(TriggerFunction):
    """Repeat a string.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, count: int):
        super().__init__("repeat", value, count)


class Replace(TriggerFunction):
    """Find the pattern in the value and replace with replacement.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, pattern: str, replacement: str):
        super().__init__("replace", value, pattern, replacement)


class Right(TriggerFunction):
    """Return the rightmost characters of the value.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, count: int):
        super().__init__("right", value, count)


class Rtrim(TriggerFunction):
    """Remove specified characters from the end of string.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, characters: str | None = None):
        super().__init__("rtrim", value, characters)


class Trim(TriggerFunction):
    """Remove specified characters from the beginning and end of string.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, characters: str | None = None):
        super().__init__("trim", value, characters)


class Xmlxpath(TriggerFunction):
    """Return the XML XPath result.

    Zabbix group: String functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/string
    """
    def __init__(self, value: TriggerExpr, path: str, default: str | None = None):
        super().__init__("xmlxpath", value, path, default)
