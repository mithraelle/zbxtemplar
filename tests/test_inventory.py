import pytest

from zbxtemplar.zabbix import Host, HostGroup, InventoryField, InventoryMode
from zbxtemplar.zabbix.Item import ValueType
from zbxtemplar.zabbix.Template import Template, TemplateGroup


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


def test_inventory_api_accepts_strings_and_validates():
    host = Host("inventory-host", groups=[HostGroup("Hosts")])
    item = Template("Inventory Template", groups=[TemplateGroup("Templates")]).add_item(
        "OS version",
        "system.sw.os",
        value_type=ValueType.CHAR,
    )

    host.set_inventory_mode("MANUAL")
    host.set_inventory("contact", "ops@example.com")
    item.set_inventory_link("os")

    assert host.to_dict()["inventory_mode"] == "MANUAL"
    assert host.to_dict()["inventory"]["contact"] == "ops@example.com"
    assert item.to_dict()["inventory_link"] == "os"

    with pytest.raises(ValueError):
        host.set_inventory_mode("NOPE")
    with pytest.raises(ValueError):
        host.set_inventory("not_a_field", "x")
    with pytest.raises(ValueError):
        item.set_inventory_link("not_a_field")


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
