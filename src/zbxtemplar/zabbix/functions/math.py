from zbxtemplar.zabbix.trigger_expression import TriggerExpr, TriggerFunction


class Abs(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("abs", value)


class Acos(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("acos", value)


class Asin(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("asin", value)


class Atan(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("atan", value)


class Atan2(TriggerFunction):
    def __init__(self, value: TriggerExpr, abscissa: TriggerExpr):
        super().__init__("atan2", value, abscissa)


class Avg(TriggerFunction):
    def __init__(self, *values: TriggerExpr):
        super().__init__("avg", *values)


class Cbrt(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("cbrt", value)


class Ceil(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("ceil", value)


class Cos(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("cos", value)


class Cosh(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("cosh", value)


class Cot(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("cot", value)


class Degrees(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("degrees", value)


class E(TriggerFunction):
    def __init__(self):
        super().__init__("e")


class Exp(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("exp", value)


class Expm1(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("expm1", value)


class Floor(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("floor", value)


class Log(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("log", value)


class Log10(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("log10", value)


class Max(TriggerFunction):
    def __init__(self, *values: TriggerExpr):
        super().__init__("max", *values)


class Min(TriggerFunction):
    def __init__(self, *values: TriggerExpr):
        super().__init__("min", *values)


class Mod(TriggerFunction):
    def __init__(self, value: TriggerExpr, divisor: TriggerExpr):
        super().__init__("mod", value, divisor)


class Pi(TriggerFunction):
    def __init__(self):
        super().__init__("pi")


class Power(TriggerFunction):
    def __init__(self, value: TriggerExpr, power: TriggerExpr):
        super().__init__("power", value, power)


class Radians(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("radians", value)


class Rand(TriggerFunction):
    def __init__(self):
        super().__init__("rand")


class Round(TriggerFunction):
    def __init__(self, value: TriggerExpr, precision: int | None = None):
        super().__init__("round", value, precision)


class Signum(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("signum", value)


class Sin(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("sin", value)


class Sinh(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("sinh", value)


class Sqrt(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("sqrt", value)


class Sum(TriggerFunction):
    def __init__(self, *values: TriggerExpr):
        super().__init__("sum", *values)


class Tan(TriggerFunction):
    def __init__(self, value: TriggerExpr):
        super().__init__("tan", value)


class Truncate(TriggerFunction):
    def __init__(self, value: TriggerExpr, precision: int | None = None):
        super().__init__("truncate", value, precision)