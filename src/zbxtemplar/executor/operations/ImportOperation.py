import hashlib
import os

from zabbix_utils import APIRequestError
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log
from zbxtemplar.modules.Context import Context


class ImportOperation(Executor):
    _OMIT_FROM_SCHEMA_DOCS = True

    _IMPORT_RULES = {
        "template_groups": {"createMissing": True, "updateExisting": True},
        "templates": {"createMissing": True, "updateExisting": True},
        "host_groups": {"createMissing": True, "updateExisting": True},
        "hosts": {"createMissing": True, "updateExisting": True},
        "valueMaps": {"createMissing": True, "updateExisting": True},
        "items": {"createMissing": True, "updateExisting": True},
        "triggers": {"createMissing": True, "updateExisting": True},
        "graphs": {"createMissing": True, "updateExisting": True},
        "templateDashboards": {"createMissing": True, "updateExisting": True},
        "mediaTypes": {"createMissing": True, "updateExisting": True},
        "templateLinkage": {"createMissing": True, "deleteMissing": True},
    }

    def _apply_file(self, path):
        resolved_path = self._resolve_path(path)
        with open(resolved_path) as f:
            yaml_content = f.read()
        sha256 = hashlib.sha256(yaml_content.encode()).hexdigest()
        size = os.path.getsize(resolved_path)
        log.input_loaded(path, sha256=sha256, bytes=size)
        try:
            self._api.configuration.import_(
                source=yaml_content, format="yaml", rules=self._IMPORT_RULES
            )
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to import '{path}': {e}") from e
        log.api_result("configuration.import", result="ok", path=path)
        ctx = Context()
        ctx.load(resolved_path)

        def _ids(api_obj, names, id_field):
            if not names:
                return {}
            rows = api_obj.get(filter={"name": list(names)}, output=[id_field, "name"])
            return {r["name"]: r[id_field] for r in rows}

        tg_ids = _ids(self._api.templategroup, ctx._template_groups, "groupid")
        hg_ids = _ids(self._api.hostgroup, ctx._host_groups, "groupid")
        t_ids  = _ids(self._api.template, ctx._templates, "templateid")
        h_ids  = _ids(self._api.host, ctx._hosts, "hostid")

        for name in ctx._template_groups:
            log.entity_end("template_group", action="import", name=name, id=tg_ids.get(name))
        for name in ctx._host_groups:
            log.entity_end("host_group", action="import", name=name, id=hg_ids.get(name))
        for name in ctx._templates:
            log.entity_end("template", action="import", name=name, id=t_ids.get(name))
        for name in ctx._hosts:
            log.entity_end("host", action="import", name=name, id=h_ids.get(name))

    def from_data(self, data):
        self._files = data if isinstance(data, list) else [data]

    def action_info(self):
        return {"files": len(self._files)}

    def execute(self):
        for path in self._files:
            self._apply_file(path)