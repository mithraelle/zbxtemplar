from zbxtemplar.decree.Token import Token
from zbxtemplar.dicts.Scroll import UserToken
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.TokenProvisioner import TokenProvisioner, TokenProvisionerError
from zbxtemplar.executor.log import log


class TokenOperation(Executor):
    """Issue API tokens for existing users without creating or updating the users."""

    def __init__(self, spec: list[UserToken], api, base_dir=None):
        super().__init__(spec, api, base_dir)

    def _validate(self):
        TokenProvisioner(self._api, self._base_dir).validate(self._spec)

    def execute(self):
        provisioner = TokenProvisioner(self._api, self._base_dir)
        usernames = [entry.username for entry in self._spec]
        existing = {
            u["username"]: u["userid"]
            for u in self._api.user.get(output=["userid", "username"], filter={"username": usernames})
        }
        log.lookup_end("users", count=len(existing))

        missing = [name for name in usernames if name not in existing]
        if missing:
            raise ValueError(f"User(s) not found in Zabbix: {', '.join(missing)}")

        for entry in self._spec:
            try:
                updated = provisioner.provision(entry.token, existing[entry.username], force=entry.force_token)
            except TokenProvisionerError as e:
                raise TokenProvisionerError(
                    f"User '{entry.username}' token '{entry.token.name}': {e}"
                ) from e
            action = "updated" if updated else "created"
            extra = {"token_name": entry.token.name, "owner": entry.username, "result": action, "secret_redacted": True}
            if entry.token.store_at != Token.STDOUT:
                extra["store_at"] = str(entry.token.store_at)
            log.secret_write("api_token", **extra)
