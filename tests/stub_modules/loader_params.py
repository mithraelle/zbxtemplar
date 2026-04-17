from zbxtemplar.modules import DecreeModule, TemplarModule


class ParamTemplar(TemplarModule):
    def __init__(self, label: str, n: int, x: float, active: bool):
        super().__init__()
        self.label = label
        self.n = n
        self.x = x
        self.active = active


class ParamDecree(DecreeModule):
    def __init__(self, label: str, n: int, x: float, active: bool):
        super().__init__()
        self.label = label
        self.n = n
        self.x = x
        self.active = active
