from zabbix_utils import APIRequestError

from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log


class SuperAdminOperation(Executor):
    """Update the currently authenticated super admin — password, username, or both."""

    def from_data(self, data):
        data = self._resolve_env(data)
        self._username = data.get("username")
        self._password = data.get("password")
        self._current_password = data.get("current_password")
        if self._password and not self._current_password:
            raise ValueError("current_password is required when changing password")

    def execute(self):
        log.entity_plan(
            "super_admin",
            password_change=bool(self._password),
            username_change=bool(self._username),
        )
        use_token = self._api._ZabbixAPI__use_token
        session_id = self._api._ZabbixAPI__session_id
        if use_token:
            auth_resp = self._api.user.checkAuthentication(token=session_id)
        else:
            auth_resp = self._api.user.checkAuthentication(sessionid=session_id)
        userid = auth_resp["userid"]
        # Fetch username before update — session dies after password change
        login_user = self._username
        if self._password and not use_token and not login_user:
            login_user = self._api.user.get(output=["username"], userids=[userid])[0]["username"]
        params = {"userid": userid}
        if self._password:
            params["passwd"] = self._password
            params["current_passwd"] = self._current_password
        if self._username:
            params["username"] = self._username
        try:
            self._api.user.update(**params)
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to update super admin: {e}") from e
        log.entity_end("super_admin", action="update", id=userid)
        if self._password and not use_token:
            self._api.login(user=login_user, password=self._password)