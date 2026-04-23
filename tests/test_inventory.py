import pytest

from zbxtemplar.zabbix import Host, HostGroup, InventoryMode
from zbxtemplar.catalog.zabbix_7_4 import InventoryField


def test_manual_inventory_exports_mode_and_fields():
    host = Host("inventory-host", groups=[HostGroup("Hosts")])
    host.set_inventory_mode(InventoryMode.MANUAL)
    host.set_inventory(InventoryField.LOCATION, "DC1 Rack 12")
    host.set_inventory(InventoryField.CONTACT, "ops@example.com")

    data = host.to_dict()

    assert data["inventory_mode"] == "MANUAL"
    assert data["inventory"] == {
        "location": "DC1 Rack 12",
        "contact": "ops@example.com",
    }


def test_inventory_data_requires_explicit_mode():
    host = Host("inventory-host", groups=[HostGroup("Hosts")])
    host.set_inventory(InventoryField.LOCATION, "DC1 Rack 12")

    with pytest.raises(ValueError, match="inventory_mode is not set"):
        host.to_dict()


def test_disabled_mode_with_fields_raises():
    host = Host("inventory-host", groups=[HostGroup("Hosts")])
    host.set_inventory_mode(InventoryMode.DISABLED)
    host.set_inventory(InventoryField.LOCATION, "DC1 Rack 12")

    with pytest.raises(ValueError, match="inventory fields"):
        host.to_dict()
