from dataclasses import dataclass
from enum import Enum


class DiffKind(Enum):
    CHANGED = "changed"
    ADDED = "added"
    MISSING = "missing"
    TYPE_MISMATCH = "type_mismatch"


@dataclass
class Diff:
    path: str    # dot-separated: "user_group.Operations.gui_access"
    local: str | list[str] | None   # value from Context (None when only on the server)
    remote: str | list[str] | None  # value from APIContext (None when only in the files)


class Inquest:
    def __init__(self, files: list[str]):
        from zbxtemplar.modules import Context
        self._ctx = Context()
        for f in files:
            self._ctx.load(f)

    def check(self, comparator, api) -> list[Diff]:
        from zbxtemplar.modules import APIContext
        api_ctx = APIContext.from_context(self._ctx, api)
        return comparator.compare(self._ctx, api_ctx)