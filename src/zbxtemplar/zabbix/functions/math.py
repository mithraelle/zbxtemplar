from zbxtemplar.zabbix.trigger_expression import TriggerExpr, TriggerFunction


class Abs(TriggerFunction):
    """The absolute value of a value.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("abs", value)


class Acos(TriggerFunction):
    """The arccosine of a value as an angle, expressed in radians.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("acos", value)


class Asin(TriggerFunction):
    """The arcsine of a value as an angle, expressed in radians.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("asin", value)


class Atan(TriggerFunction):
    """The arctangent of a value as an angle, expressed in radians.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("atan", value)


class Atan2(TriggerFunction):
    """The arctangent of the ordinate (value) and abscissa coordinates specified as an angle,
    expressed in radians.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr, abscissa: TriggerExpr):
        super().__init__("atan2", value, abscissa)


class Avg(TriggerFunction):
    """The average value of the referenced item values.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, *values: TriggerExpr):
        super().__init__("avg", *values)


class Cbrt(TriggerFunction):
    """The cube root of a value.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("cbrt", value)


class Ceil(TriggerFunction):
    """Round the value up to the nearest greater or equal integer.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("ceil", value)


class Cos(TriggerFunction):
    """The cosine of a value, where the value is an angle expressed in radians.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("cos", value)


class Cosh(TriggerFunction):
    """The hyperbolic cosine of a value.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("cosh", value)


class Cot(TriggerFunction):
    """The cotangent of a value, where the value is an angle expressed in radians.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("cot", value)


class Degrees(TriggerFunction):
    """Converts a value from radians to degrees.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("degrees", value)


class E(TriggerFunction):
    """Euler's number (2.718281828459045).

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self):
        super().__init__("e")


class Exp(TriggerFunction):
    """Euler's number at a power of a value.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("exp", value)


class Expm1(TriggerFunction):
    """Euler's number at a power of a value minus 1.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("expm1", value)


class Floor(TriggerFunction):
    """Round the value down to the nearest smaller or equal integer.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("floor", value)


class Log(TriggerFunction):
    """The natural logarithm.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("log", value)


class Log10(TriggerFunction):
    """The decimal logarithm.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("log10", value)


class Max(TriggerFunction):
    """The highest value of the referenced item values.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, *values: TriggerExpr):
        super().__init__("max", *values)


class Min(TriggerFunction):
    """The lowest value of the referenced item values.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, *values: TriggerExpr):
        super().__init__("min", *values)


class Mod(TriggerFunction):
    """The division remainder.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr, divisor: TriggerExpr):
        super().__init__("mod", value, divisor)


class Pi(TriggerFunction):
    """The Pi constant (3.14159265358979).

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self):
        super().__init__("pi")


class Power(TriggerFunction):
    """The power of a value.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr, power: TriggerExpr):
        super().__init__("power", value, power)


class Radians(TriggerFunction):
    """Converts a value from degrees to radians.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("radians", value)


class Rand(TriggerFunction):
    """Return a random integer value.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self):
        super().__init__("rand")


class Round(TriggerFunction):
    """Round the value to decimal places.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr, precision: int | None = None):
        super().__init__("round", value, precision)


class Signum(TriggerFunction):
    """Returns '-1' if a value is negative, '0' if a value is zero, '1' if a value is positive.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("signum", value)


class Sin(TriggerFunction):
    """The sine of a value, where the value is an angle expressed in radians.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("sin", value)


class Sinh(TriggerFunction):
    """The hyperbolical sine of a value, where the value is an angle expressed in radians.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("sinh", value)


class Sqrt(TriggerFunction):
    """The square root of a value.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("sqrt", value)


class Sum(TriggerFunction):
    """The sum of the referenced item values.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, *values: TriggerExpr):
        super().__init__("sum", *values)


class Tan(TriggerFunction):
    """The tangent of a value.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr):
        super().__init__("tan", value)


class Truncate(TriggerFunction):
    """Truncate the value to decimal places.

    Zabbix group: Mathematical functions
    Source: https://www.zabbix.com/documentation/current/en/manual/appendix/functions/math
    """
    def __init__(self, value: TriggerExpr, precision: int | None = None):
        super().__init__("truncate", value, precision)
