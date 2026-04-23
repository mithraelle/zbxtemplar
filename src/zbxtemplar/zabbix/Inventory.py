from __future__ import annotations

from enum import StrEnum
from typing import Any


class InventoryMode(StrEnum):
    """Zabbix host inventory mode."""

    DISABLED = "DISABLED"
    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"


InventoryMode._API_VALUES = {"DISABLED": -1, "MANUAL": 0, "AUTOMATIC": 1}


class InventoryField(StrEnum):
    """Placeholder base for host inventory field names. Concrete members live in versioned catalogs (e.g. `zbxtemplar.catalog.zabbix_7_4.InventoryField`)."""


class WithInventory:
    def __init__(self):
        super().__init__()
        self.inventory_mode: InventoryMode | None = None
        self.inventory: dict[str, Any] = {}

    def set_inventory_mode(self, mode: InventoryMode):
        """Set the host inventory mode (`DISABLED`, `MANUAL`, or `AUTOMATIC`)."""
        self.inventory_mode = mode
        return self

    def set_inventory(self, field: InventoryField, value: Any):
        """Set a single inventory field. Pass an `InventoryField` member from a versioned catalog."""
        self.inventory[str(field)] = value
        return self
