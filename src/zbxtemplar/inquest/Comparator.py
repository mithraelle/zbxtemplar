from enum import Enum

from zbxtemplar.dicts.Schema import FieldPolicy, SchemaField, SubsetBy
from zbxtemplar.inquest import Diff
from zbxtemplar.modules import Context, APIContext

_SCALAR_TYPES = (str, int, float, bool, bytes, Enum, type(None))


class Comparator:
    def compare(self, ctx: Context, api_ctx: APIContext) -> list[Diff]:
        registries = [
            ("user_group",  ctx._user_groups,       api_ctx._user_groups),
            ("user",        ctx._users,             api_ctx._users),
            ("encryption",  ctx._host_encryptions,  api_ctx._host_encryptions),
            ("action",      ctx._actions,           api_ctx._actions),
        ]
        diffs = []
        for label, local, remote in registries:
            if local is not None:
                diffs += self._compare_registry(label, local, remote)
        if ctx._saml is not None:
            if api_ctx._saml is None:
                diffs.append(Diff("saml", ctx._saml, None))
            else:
                diffs += self._compare_entity(ctx._saml, api_ctx._saml, "saml")
        return diffs

    def _compare_registry(self, label: str, local, remote) -> list[Diff]:
        diffs = self._compare_list(label, local.keys(), remote.keys())
        for name in local.keys() & remote.keys():
            diffs += self._compare_entity(local[name], remote[name], f"{label}.{name}")
        return diffs

    def _compare_list(self, label: str, local, remote) -> list[Diff]:
        local, remote = set(local or []), set(remote or [])
        diffs = []
        only_local = local - remote
        if only_local:
            diffs.append(Diff(label, sorted(only_local), None))
        only_remote = remote - local
        if only_remote:
            diffs.append(Diff(label, None, sorted(only_remote)))
        return diffs

    def _compare_list_key(self, local, remote, path, key) -> list[Diff]:
        l_by = {getattr(x, key): x for x in local or []}
        r_by = {getattr(x, key): x for x in remote or []}
        diffs = self._compare_list(path, l_by.keys(), r_by.keys())
        for k in l_by.keys() & r_by.keys():
            diffs += self._compare_entity(l_by[k], r_by[k], f"{path}[{k}]")
        return diffs

    def _compare_entity(self, local, remote, path) -> list[Diff]:
        diffs = []
        if getattr(local, '_SCHEMA', None):
            fields = local._SCHEMA
        else:
            l_keys = set(local.keys()) if isinstance(local, dict) else {k for k in vars(local) if not k.startswith('_')}
            r_keys = set(remote.keys()) if isinstance(remote, dict) else {k for k in vars(remote) if not k.startswith('_')}
            diffs += self._compare_list(path, l_keys, r_keys)
            fields = [SchemaField(key=k) for k in l_keys & r_keys]

        for field in fields:
            key = field.key
            lv = local[key] if isinstance(local, dict) else getattr(local, key, None)
            rv = remote[key] if isinstance(remote, dict) else getattr(remote, key, None)
            child = f"{path}.{key}"
            if not self._should_compare(lv, rv, field):
                continue
            if isinstance(lv, list):
                if isinstance(field.policy, SubsetBy):
                    diffs += self._compare_list_key(lv, rv, child, field.policy.key)
                else:
                    diffs += self._compare_list(child, lv, rv)
            elif isinstance(lv, _SCALAR_TYPES):
                if lv != rv:
                    diffs.append(Diff(child, lv, rv))
            else:
                diffs += self._compare_entity(lv, rv, child)
        return diffs

    def _should_compare(self, local, remote, field: SchemaField) -> bool:
        raise NotImplementedError


class RawDiff(Comparator):
    def _should_compare(self, local, remote, field: SchemaField) -> bool:
        return True


class SchemaDiff(Comparator):
    def _should_compare(self, local, remote, field: SchemaField) -> bool:
        if field.policy == FieldPolicy.IGNORE:
            return False
        d = field.api_default
        if d is not None and local in (None, "") and (
            set(remote) == set(d) if isinstance(remote, list) else remote == d
        ):
            return False
        return True