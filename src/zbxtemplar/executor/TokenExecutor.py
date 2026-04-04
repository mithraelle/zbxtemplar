import os

from zbxtemplar.decree.Token import TokenOutput, TokenExpiry


class TokenExecutorError(Exception):
    """Raised by internal TokenExecutor methods — contextualized by provision_user."""
    pass


class TokenExecutor:
    def __init__(self, api, resolve_path):
        self._resolve_path = resolve_path
        self._api = api

    def validate(self, users):
        seen_names = {}
        seen_paths = {}

        for user in users:
            if not user.token:
                continue

            name = user.token.name
            if name in seen_names:
                raise TokenExecutorError(
                    f"Duplicate token name '{name}': "
                    f"users '{seen_names[name]}' and '{user.username}'"
                )
            seen_names[name] = user.username

            if user.token.store_at is TokenOutput.STDOUT:
                continue

            path = os.path.normcase(os.path.abspath(self._resolve_path(user.token.store_at)))
            if path in seen_paths:
                raise TokenExecutorError(
                    f"Duplicate store_at path '{user.token.store_at}': "
                    f"users '{seen_paths[path]}' and '{user.username}'"
                )
            seen_paths[path] = user.username
            if os.path.exists(path):
                raise TokenExecutorError(
                    f"User '{user.username}': "
                    f"refusing to overwrite existing file '{user.token.store_at}'"
                )

    @staticmethod
    def _expiration_for_api(token, *, creating):
        if token.expires_at is None:
            if creating:
                raise TokenExecutorError("token.expires_at is required on create")
            return None
        if token.expires_at is TokenExpiry.NEVER:
            return 0
        return token.expires_at

    @staticmethod
    def _extract_secret(generate_result):
        if isinstance(generate_result, list):
            if not generate_result:
                raise TokenExecutorError("token.generate returned an empty list")
            generate_result = generate_result[0]
        secret = (generate_result or {}).get("token")
        if not secret:
            raise TokenExecutorError("token.generate did not return a secret")
        return secret

    def _extract_tokenid(self, create_result, token_name, userid):
        tokenids = (create_result or {}).get("tokenids")
        if tokenids:
            return tokenids[0]
        matches = self._api.token.get(
            output=["tokenid"],
            userids=userid,
            filter={"name": token_name},
        )
        if not matches:
            raise TokenExecutorError(f"unable to resolve token id for '{token_name}'")
        return matches[0]["tokenid"]

    def _find_existing_token(self, token_name, userid):
        matches = self._api.token.get(
            output=["tokenid", "name", "userid", "expires_at", "status"],
            filter={"name": token_name},
        )
        for match in matches:
            if str(match.get("userid")) != str(userid):
                raise TokenExecutorError(
                    f"token '{token_name}' belongs to a different user"
                )
        if len(matches) > 1:
            raise TokenExecutorError(f"multiple tokens named '{token_name}' found")
        return matches[0] if matches else None

    def _write_secret(self, path, secret):
        resolved = self._resolve_path(path)
        parent = os.path.dirname(resolved)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(resolved, "x", encoding="utf-8") as f:
            f.write(secret)

    def provision(self, token, userid, force=False):
        token_name = token.name
        existing_token = self._find_existing_token(token_name, userid)

        if existing_token:
            if not force:
                raise TokenExecutorError(
                    f"token '{token_name}' already exists. "
                    f"Set force_token: true to update it."
                )
            update_params = {"tokenid": existing_token["tokenid"], "status": 0}
            expires_at = self._expiration_for_api(token, creating=False)
            if expires_at is not None:
                update_params["expires_at"] = expires_at
            self._api.token.update(**update_params)
            tokenid = existing_token["tokenid"]
        else:
            expires_at = self._expiration_for_api(token, creating=True)
            create_result = self._api.token.create(
                name=token_name,
                userid=userid,
                expires_at=expires_at,
            )
            tokenid = self._extract_tokenid(create_result, token_name, userid)

        secret = self._extract_secret(
            self._api.token.generate(tokenid=tokenid),
        )

        if token.store_at is TokenOutput.STDOUT:
            print(secret)
        else:
            self._write_secret(token.store_at, secret)

        return existing_token is not None
