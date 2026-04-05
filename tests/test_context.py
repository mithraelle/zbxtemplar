import pytest

from zbxtemplar.modules import Context
from tests.paths import FIXTURES_DIR, REFERENCE_DIR


class TestZabbixExport:
    def test_template_groups(self):
        ctx = Context().load(str(REFERENCE_DIR / "templates.yml"))
        tg = ctx.get_template_group("Templar Templates")
        assert tg.name == "Templar Templates"

    def test_template_group_missing(self):
        ctx = Context().load(str(REFERENCE_DIR / "templates.yml"))
        with pytest.raises(ValueError, match="not found in context"):
            ctx.get_template_group("Nonexistent")

    def test_host_groups(self):
        ctx = Context().load(str(REFERENCE_DIR / "hosts.yml"))
        hg = ctx.get_host_group("Templar Hosts")
        assert hg.name == "Templar Hosts"

    def test_macros_from_templates(self):
        ctx = Context().load(str(REFERENCE_DIR / "templates.yml"))
        tmpl = ctx.get_template("Test Template")
        assert "MY_MACRO" in tmpl.macros

    def test_combined_file(self):
        ctx = Context().load(str(REFERENCE_DIR / "combined.yml"))

        # template group
        tg = ctx.get_template_group("Templar Templates")
        assert tg.name == "Templar Templates"

        # host group
        hg = ctx.get_host_group("Templar Hosts")
        assert hg.name == "Templar Hosts"

        # template with macros, tags, items
        tmpl = ctx.get_template("Test Template")
        assert tmpl.name == "Test Template"
        assert tmpl.groups[0] is tg
        assert "MY_MACRO" in tmpl.macros
        assert tmpl.macros["MY_MACRO"].value == "1"
        assert any(t.name == "Service" for t in tmpl.tags.values())
        assert len(tmpl.items) == 3
        item1 = next(i for i in tmpl.items if i.key == "item.test[1]")
        assert item1.name == "Item 1"
        assert any(t.name == "Service" for t in item1.tags.values())
        assert len(item1.triggers) == 1
        assert item1.triggers[0].name == "Simple trigger"
        assert item1.triggers[0].priority.value == "HIGH"

        # host with macros, tags, items, linked template
        host = ctx.get_host("Templar Host")
        assert host.name == "Templar Host"
        assert host.groups[0] is hg
        assert "MY_HOST_MACRO" in host.macros
        assert len(host.templates) == 1
        assert host.templates[0] is tmpl
        assert len(host.items) == 1
        host_item = host.items[0]
        assert host_item.key == "item.test[own]"
        assert len(host_item.triggers) == 1
        assert host_item.triggers[0].name == "Host Simple trigger"

        # root-level triggers attached to their owners
        tmpl_trigger_names = [t.name for t in tmpl.triggers]
        assert "Complex trigger" in tmpl_trigger_names
        host_trigger_names = [t.name for t in host.triggers]
        assert "Host Complex trigger" in host_trigger_names


class TestDecree:
    def test_user_group(self):
        ctx = Context().load(str(FIXTURES_DIR / "user_group.decree.yml"))
        ug = ctx.get_user_group("Templar Users")
        assert ug.name == "Templar Users"

    def test_user_group_collects_host_groups(self):
        ctx = Context().load(str(FIXTURES_DIR / "user_group.decree.yml"))
        ctx.get_host_group("Linux servers")
        ctx.get_host_group("Virtual machines")

    def test_user_group_collects_template_groups(self):
        ctx = Context().load(str(FIXTURES_DIR / "user_group.decree.yml"))
        ctx.get_template_group("Test Template")

    def test_add_user_collects_groups(self):
        ctx = Context().load(str(FIXTURES_DIR / "add_user.yml"))
        ctx.get_user_group("Templar Users")


class TestSetMacro:
    def test_macro_names(self):
        ctx = Context().load(str(FIXTURES_DIR / "set_macro.yml"))
        ctx.get_macro("{$SNMP_COMMUNITY}")
        ctx.get_macro("{$DB_PASSWORD}")


class TestMultipleLoads:
    def test_accumulates(self):
        ctx = Context()
        ctx.load(str(REFERENCE_DIR / "templates.yml"))
        ctx.load(str(REFERENCE_DIR / "hosts.yml"))
        ctx.load(str(FIXTURES_DIR / "set_macro.yml"))
        ctx.load(str(FIXTURES_DIR / "user_group.decree.yml"))
        ctx.get_template_group("Templar Templates")
        ctx.get_template_group("Test Template")
        ctx.get_host_group("Linux servers")
        ctx.get_host_group("Templar Hosts")
        ctx.get_host_group("Virtual machines")
        ctx.get_user_group("Templar Users")
        ctx.get_macro("{$SNMP_COMMUNITY}")

    def test_chaining(self):
        ctx = (Context()
               .load(str(REFERENCE_DIR / "templates.yml"))
               .load(str(FIXTURES_DIR / "user_group.decree.yml")))
        ctx.get_template_group("Templar Templates")
        ctx.get_template_group("Test Template")
        ctx.get_user_group("Templar Users")


    def test_reverse_order_preserves_identity(self):
        """Host loaded first creates a stub template; templates loaded second upgrades in-place.
        Host object keeps its reference to the same template object."""
        ctx = Context()
        ctx.load(str(REFERENCE_DIR / "hosts.yml"))

        host = ctx.get_host("Templar Host")
        linked_tmpl = host.templates[0]
        assert linked_tmpl.name == "Test Template"
        assert len(linked_tmpl.items) == 0  # stub — no items yet

        # Load templates — should upgrade the stub, not replace it
        ctx.load(str(REFERENCE_DIR / "templates.yml"))

        tmpl_rich = ctx.get_template("Test Template")
        assert tmpl_rich is linked_tmpl  # same object
        assert len(linked_tmpl.items) == 3  # now has items
        assert host.templates[0] is tmpl_rich  # host still points to it

    def test_reverse_order_host_group_upgraded(self):
        """Host group stub from hosts file gets upgraded when combined file reloads it."""
        ctx = Context()
        ctx.load(str(REFERENCE_DIR / "hosts.yml"))

        hg = ctx.get_host_group("Templar Hosts")
        host = ctx.get_host("Templar Host")
        assert host.groups[0] is hg

        # Reload from combined — same host group should be upgraded in-place
        ctx.load(str(REFERENCE_DIR / "combined.yml"))

        hg_after = ctx.get_host_group("Templar Hosts")
        assert hg_after is hg
        assert host.groups[0] is hg  # host still references the same object


class TestUnknownFormat:
    def test_scroll_rejected(self):
        with pytest.raises(ValueError, match="unknown format"):
            Context().load(str(FIXTURES_DIR / "scroll.yml"))

    def test_error_shows_keys(self):
        with pytest.raises(ValueError, match="stages"):
            Context().load(str(FIXTURES_DIR / "scroll.yml"))

