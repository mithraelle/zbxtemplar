from zabbix_utils import APIRequestError

from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError


class SuperAdminOperation(Executor):
    _OMIT_FROM_SCHEMA_DOCS = True

    def from_data(self, data):
        data = self._resolve_env(data)
        self._password = data if isinstance(data, str) else data["password"]

    def execute(self):
        print("Updating super admin password...")
        try:
            self._api.user.update(userid="1", passwd=self._password)
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to update super admin password: {e}") from e