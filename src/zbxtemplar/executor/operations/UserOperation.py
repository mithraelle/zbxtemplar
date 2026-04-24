from zbxtemplar.decree import User, Severity
from zbxtemplar.decree.Token import Token
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.TokenProvisioner import TokenProvisioner, TokenProvisionerError
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log
from zabbix_utils import APIRequestError


class UserOperation(Executor):
    def __init__(self, spec: list[User], api, base_dir=None):
        super().__init__(spec, api, base_dir)

    def _validate(self):
        token_executor = TokenProvisioner(self._api, self._base_dir)
        token_executor.validate(self._spec)

    def execute(self):
        token_executor = TokenProvisioner(self._api, self._base_dir)
        roles = {r["name"]: r["roleid"] for r in self._api.role.get(output=["roleid", "name"])}
        ugroups = {g["name"]: g["usrgrpid"] for g in self._api.usergroup.get(output=["usrgrpid", "name"])}
        media_types = {m["name"]: m["mediatypeid"] for m in self._api.mediatype.get(output=["mediatypeid", "name"])}
        existing = {u["username"]: u["userid"] for u in self._api.user.get(output=["userid", "username"])}
        log.lookup_end("users", count=len(existing))

        for user in self._spec:
            if user.role not in roles:
                raise ValueError(f"Role '{user.role}' not found in Zabbix")
            params = {"username": user.username, "roleid": roles[user.role]}

            if user.password:
                params["passwd"] = user.password

            if user.groups:
                usrgrps = []
                for gname in user.groups:
                    if gname not in ugroups:
                        raise ValueError(f"User group '{gname}' not found in Zabbix")
                    usrgrps.append({"usrgrpid": ugroups[gname]})
                params["usrgrps"] = usrgrps

            if user.medias:
                medias = []
                for m in user.medias:
                    if m.type not in media_types:
                        raise ValueError(f"Media type '{m.type}' not found in Zabbix")
                    media = {"mediatypeid": media_types[m.type], "sendto": m.sendto}
                    if m.severity is not None:
                        media["severity"] = Severity.mask(m.severity)
                    if m.period is not None:
                        media["period"] = m.period
                    medias.append(media)
                params["medias"] = medias

            if user.username in existing:
                params["userid"] = existing[user.username]
                del params["username"]
                try:
                    self._api.user.update(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to update user '{user.username}': {e}") from e
                log.entity_end("user", action="update", username=user.username, id=existing[user.username])
            else:
                try:
                    create_result = self._api.user.create(**params)
                except APIRequestError as e:
                    raise ExecutorApiError(f"Failed to create user '{user.username}': {e}") from e
                userids = (create_result or {}).get("userids")
                if not userids:
                    raise ValueError(f"Unable to resolve created user id for '{user.username}'")
                existing[user.username] = userids[0]
                log.entity_end(
                    "user", action="create",
                    username=user.username,
                    id=userids[0],
                    role=user.role,
                    groups=len(user.groups) if user.groups else 0,
                )

            if user.token:
                try:
                    updated = token_executor.provision(
                        user.token, existing[user.username], force=user.force_token
                    )
                    action = "updated" if updated else "created"
                    extra = {"token_name": user.token.name, "owner": user.username, "result": action, "secret_redacted": True}
                    if user.token.store_at != Token.STDOUT:
                        extra["store_at"] = str(user.token.store_at)
                    log.secret_write("api_token", **extra)
                except TokenProvisionerError as e:
                    raise TokenProvisionerError(
                        f"User '{user.username}' token '{user.token.name}': {e}"
                    ) from e
