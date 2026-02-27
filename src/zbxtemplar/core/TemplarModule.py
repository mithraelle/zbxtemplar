import inspect
import importlib.util
import os

import zbxtemplar.core.ZbxEntity as _zbx


class TemplarModule:
    def __init__(self):
        self.templates = []
        self.graphs = []

    def to_export(self, version: str = "7.4") -> dict:
        groups = {}
        for t in self.templates:
            for g in t.groups:
                groups[g.name] = g

        export = {
            "zabbix_export": {
                "version": version,
                "template_groups": [
                    g.to_dict()
                    for g in sorted(groups.values(), key=lambda g: g.name)
                ],
                "templates": [t.to_dict() for t in self.templates],
            }
        }
        triggers = []
        for t in self.templates:
            triggers += t.triggers
        if triggers:
            export["zabbix_export"]["triggers"] = [t.to_dict() for t in triggers]
        if self.graphs:
            export["zabbix_export"]["graphs"] = [g.to_dict() for g in self.graphs]
        return export


def load_module(filename: str) -> dict:
    mod_name = os.path.splitext(os.path.basename(filename))[0]
    spec = importlib.util.spec_from_file_location(mod_name, filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    result = {}
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if issubclass(obj, TemplarModule) and obj is not TemplarModule:
            result[name] = obj()
    return result