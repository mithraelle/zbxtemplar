from zbxtemplar.modules import DecreeModule, TemplarModule


class ParamTemplar(TemplarModule):
    def compose(self, label: str, n: int, x: float, active: bool):
        self.label = label
        self.n = n
        self.x = x
        self.active = active


class ParamDecree(DecreeModule):
    def compose(self, label: str, n: int, x: float, active: bool):
        self.label = label
        self.n = n
        self.x = x
        self.active = active
