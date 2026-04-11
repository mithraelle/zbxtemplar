from zabbix_utils import APIRequestError

from zbxtemplar.decree.Encryption import HostEncryption, EncryptionMode
from zbxtemplar.executor.Executor import Executor
from zbxtemplar.executor.exceptions import ExecutorApiError, ExecutorParseError


class EncryptionOperation(Executor):
    def _compute_bitmap(self, modes: list[EncryptionMode]) -> int:
        bitmap = 0
        for mode in modes:
            bitmap |= mode.value
        return bitmap

    def _parse_entries(self, data) -> list[HostEncryption]:
        if isinstance(data, dict):
            nodes = [data]
        elif isinstance(data, list):
            nodes = data
        else:
            raise ExecutorParseError("Expected encryption node to be a dictionary")

        entries = []
        for node in nodes:
            defaults = node.get("host_defaults", {})
            raw_hosts = node.get("hosts", [])

            for raw_host in raw_hosts:
                merged = {**defaults, **raw_host}
                entries.append(HostEncryption.from_dict(merged))

        return entries

    def from_data(self, data):
        self._entries = self._parse_entries(data)

    def execute(self):
        if self._entries:
            self._apply(self._entries)

    def _apply(self, entries: list[HostEncryption]):
        if not entries:
            return
        # Pre-fetch all matching hosts by technical name
        host_names = [entry.host for entry in entries]
        existing_hosts = self._api.host.get(
            filter={"host": host_names},
            output=["hostid", "host", "tls_connect", "tls_accept", "tls_issuer", "tls_subject", "tls_psk_identity"]
        )

        host_map = {h["host"]: h for h in existing_hosts}

        for entry in entries:
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

            print(f"Updating encryption settings for host '{entry.host}'...")
            try:
                self._api.host.update(**params)
            except APIRequestError as e:
                raise ExecutorApiError(f"Failed to update encryption for host '{entry.host}': {e}") from e