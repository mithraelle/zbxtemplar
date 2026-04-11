from zabbix_utils import APIRequestError

from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError


class ImportOperation(Executor):
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
        print(f"Importing {path}...")
        try:
            self._api.configuration.import_(
                source=yaml_content, format="yaml", rules=self._IMPORT_RULES
            )
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to import '{path}': {e}") from e

    def from_data(self, data):
        self._files = data if isinstance(data, list) else [data]

    def execute(self):
        for path in self._files:
            self._apply_file(path)