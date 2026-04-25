import copy

from zabbix_utils import APIRequestError

from zbxtemplar.decree.Encryption import HostEncryption, EncryptionMode
from zbxtemplar.dicts.Decree import EncryptionDecree
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError
from zbxtemplar.executor.log import log


class EncryptionOperation(Executor):
    def __init__(self, spec: list[EncryptionDecree], api, base_dir=None):
        super().__init__(spec, api, base_dir)

    def _compute_bitmap(self, modes: list[EncryptionMode]) -> int:
        bitmap = 0
        for mode in modes:
            bitmap |= mode.api
        return bitmap

    @staticmethod
    def _merge_defaults(defaults, host: HostEncryption) -> HostEncryption:
        entry = copy.deepcopy(host)
        if defaults is None:
            entry.check()
            return entry

        if not entry.connect:
            entry.connect = copy.deepcopy(defaults.connect)
        if not entry.accept:
            entry.accept = copy.deepcopy(defaults.accept)

        modes = set((entry.connect or []) + (entry.accept or []))
        for mode, fields in entry._MODE_FIELDS.items():
            if mode not in modes:
                continue
            for field in fields:
                if getattr(entry, field) is None:
                    setattr(entry, field, getattr(defaults, field))

        entry.check()
        return entry

    def action_info(self):
        return {"items": len(self._entries)}

    def _validate(self):
        self._entries = []
        for node in self._spec:
            for host in node.hosts or []:
                self._entries.append(self._merge_defaults(node.host_defaults, host))

    def execute(self):
        if not self._entries:
            return

        # Pre-fetch all matching hosts by technical name
        host_names = [entry.host for entry in self._entries]
        existing_hosts = self._api.host.get(
            filter={"host": host_names},
            output=["hostid", "host", "tls_connect", "tls_accept", "tls_issuer", "tls_subject", "tls_psk_identity"]
        )

        host_map = {h["host"]: h for h in existing_hosts}

        for entry in self._entries:
            if entry.host not in host_map:
                raise ValueError(f"Host '{entry.host}' not found in Zabbix. Cannot configure encryption.")

            api_host = host_map[entry.host]

            desired_connect = self._compute_bitmap(entry.connect)
            desired_accept = self._compute_bitmap(entry.accept)

            # Note: Zabbix returns these as string representations of integers
            current_connect = int(api_host["tls_connect"])
            current_accept = int(api_host["tls_accept"])
            current_issuer = api_host.get("tls_issuer", "")
            current_subject = api_host.get("tls_subject", "")
            current_psk_identity = api_host.get("tls_psk_identity", "")

            desired_issuer = entry.issuer or ""
            desired_subject = entry.subject or ""
            desired_psk_identity = entry.psk_identity or ""

            # Check if an update is needed
            # We enforce an update if any field explicitly modeled mismatches.
            # Additionally, because PSK is write-only, if PSK mode is configured,
            # we always update it to ensure it hasn't drifted.
            update_needed = False

            if current_connect != desired_connect:
                update_needed = True
            elif current_accept != desired_accept:
                update_needed = True
            elif current_issuer != desired_issuer:
                update_needed = True
            elif current_subject != desired_subject:
                update_needed = True
            elif current_psk_identity != desired_psk_identity:
                update_needed = True

            all_modes = entry.connect + entry.accept
            has_psk = EncryptionMode.PSK in all_modes
            if has_psk:
                update_needed = True  # Always enforce PSK update since we can't read it natively

            if not update_needed:
                continue

            params = {
                "hostid": api_host["hostid"],
                "tls_connect": desired_connect,
                "tls_accept": desired_accept,
            }

            if has_psk:
                params["tls_psk_identity"] = desired_psk_identity
                params["tls_psk"] = entry.psk

            has_cert = EncryptionMode.CERT in all_modes
            if has_cert:
                params["tls_issuer"] = desired_issuer
                params["tls_subject"] = desired_subject
            elif current_issuer or current_subject:
                # Clear them out if migrating away from CERT mode
                params["tls_issuer"] = ""
                params["tls_subject"] = ""

            try:
                self._api.host.update(**params)
            except APIRequestError as e:
                raise ExecutorApiError(f"Failed to update encryption for host '{entry.host}': {e}") from e
            reason = "psk_write_only_enforced" if has_psk else None
            log.entity_end("encryption", action="update", host=entry.host, reason=reason)
