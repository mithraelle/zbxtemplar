from zabbix_utils import APIRequestError

from zbxtemplar.dicts.Scroll import SuperAdmin
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log


class SuperAdminOperation(Executor):
    """Update the currently authenticated super admin — password, username, or both."""

    def __init__(self, spec: SuperAdmin, api, base_dir=None):
        super().__init__(spec, api, base_dir)

    def _validate(self):
        if self._spec.password and not self._spec.current_password:
            raise ValueError("current_password is required when changing password")

    def execute(self):
        username = self._spec.username
        password = self._spec.password
        current_password = self._spec.current_password

        log.entity_plan(
            "super_admin",
            password_change=bool(password),
            username_change=bool(username),
        )
        use_token = self._api._ZabbixAPI__use_token
        session_id = self._api._ZabbixAPI__session_id
        if use_token:
            auth_resp = self._api.user.checkAuthentication(token=session_id)
        else:
            auth_resp = self._api.user.checkAuthentication(sessionid=session_id)
        userid = auth_resp["userid"]
        # Fetch username before update — session dies after password change
        login_user = username
        if password and not use_token and not login_user:
            login_user = self._api.user.get(output=["username"], userids=[userid])[0]["username"]
        params = {"userid": userid}
        if password:
            params["passwd"] = password
            params["current_passwd"] = current_password
        if username:
            params["username"] = username
        try:
            self._api.user.update(**params)
        except APIRequestError as e:
            raise ExecutorApiError(f"Failed to update super admin: {e}") from e
        log.entity_end("super_admin", action="update", id=userid)
        if password and not use_token:
            self._api.login(user=login_user, password=password)
