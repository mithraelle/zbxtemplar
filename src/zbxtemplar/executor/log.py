import json
import logging
import sys


def _fmt_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    return f'"{s}"' if " " in s else s


def _fmt_line(event, fields):
    if not fields:
        return event
    parts = " ".join(f"{k}={_fmt_value(v)}" for k, v in fields.items() if v is not None)
    return f"{event} {parts}"


class _JsonFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, "fields"):
            return json.dumps(record.fields)
        return json.dumps({"level": record.levelname.lower(), "message": record.getMessage()})


class Log:
    def __init__(self):
        self._seq = 0
        self._actions = 0
        self._created = 0
        self._updated = 0
        self._failed = 0
        self._json = False
        self._logger = logging.getLogger("zbxtemplar.executor")
        self._logger.setLevel(logging.INFO)

    def configure(self, json_output=False):
        self._json = json_output
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter() if json_output else logging.Formatter("%(message)s"))
        self._logger.handlers.clear()
        self._logger.addHandler(handler)

    def _next(self):
        self._seq += 1
        return self._seq

    def _emit(self, event, **fields):
        n = self._next()
        if self._json:
            self._logger.info("", extra={"fields": {"seq": n, "event": event, **fields}})
        else:
            self._logger.info("[%03d] %s", n, _fmt_line(event, fields))

    def _raw(self, event, **fields):
        """Emit without sequence number (run.start, run.end)."""
        if self._json:
            self._logger.info("", extra={"fields": {"event": event, **fields}})
        else:
            self._logger.info("%s", _fmt_line(event, fields))

    # --- run level ---

    def run_start(self, run_id, target, auth, base_dir=None):
        fields = {"run_id": run_id, "target": target, "auth": auth}
        if base_dir:
            fields["base_dir"] = base_dir
        self._emit("run.start", **fields)

    def run_end(self, run_id, result, actions, duration_ms):
        self._emit(
            "run.end",
            run_id=run_id,
            result=result,
            actions=actions,
            created=self._created,
            updated=self._updated,
            failed=self._failed,
            duration_ms=duration_ms,
        )

    # --- action level ---

    def action_start(self, name, **extra):
        self._emit("action.start", name=name, **extra)

    def action_end(self, name, result, duration_ms):
        self._emit("action.end", name=name, result=result, duration_ms=duration_ms)
        self._actions += 1

    # --- entity level ---

    def entity_plan(self, type, **fields):
        self._emit("entity.plan", type=type, **fields)

    def entity_end(self, type, action, result="ok", **fields):
        self._emit("entity.end", type=type, action=action, result=result, **fields)
        if result == "ok":
            if action == "create":
                self._created += 1
            elif action == "update":
                self._updated += 1
        else:
            self._failed += 1

    def lookup_end(self, type, count):
        self._emit("lookup.end", type=type, count=count)

    def input_loaded(self, path, **fields):
        self._emit("input.loaded", path=path, **fields)

    def api_result(self, method, result, **fields):
        self._emit("api.result", method=method, result=result, **fields)

    def secret_write(self, type, **fields):
        self._emit("secret.write", type=type, **fields)


log = Log()