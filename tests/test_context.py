from pathlib import Path

import pytest

from zbxtemplar.core import Context

TESTS = Path(__file__).parent


class TestZabbixExport:
    def test_template_groups(self):
        ctx = Context().load(str(TESTS / "reference_templates.yml"))
        assert ctx.get_template_group("Templar Templates") == "Templar Templates"

    def test_template_group_missing(self):
        ctx = Context().load(str(TESTS / "reference_templates.yml"))
        with pytest.raises(ValueError, match="not found in context"):
            ctx.get_template_group("Nonexistent")

    def test_host_groups(self):
        ctx = Context().load(str(TESTS / "reference_hosts.yml"))
        assert ctx.get_host_group("Templar Hosts") == "Templar Hosts"

    def test_macros_from_templates(self):
        ctx = Context().load(str(TESTS / "reference_templates.yml"))
        assert ctx.get_macro("{$MY_MACRO}") == "{$MY_MACRO}"

    def test_macros_from_hosts(self):
        ctx = Context().load(str(TESTS / "reference_hosts.yml"))
        assert ctx.get_macro("{$MY_HOST_MACRO}") == "{$MY_HOST_MACRO}"

    def test_combined_file(self):
        ctx = Context().load(str(TESTS / "reference_combined.yml"))
        ctx.get_template_group("Templar Templates")
        ctx.get_host_group("Templar Hosts")
        ctx.get_macro("{$MY_MACRO}")
        ctx.get_macro("{$MY_HOST_MACRO}")


class TestDecree:
    def test_user_group(self):
        ctx = Context().load(str(TESTS / "test_user_group.decree.yml"))
        assert ctx.get_user_group("Templar Users") == "Templar Users"

    def test_user_group_collects_host_groups(self):
        ctx = Context().load(str(TESTS / "test_user_group.decree.yml"))
        ctx.get_host_group("Linux servers")
        ctx.get_host_group("Virtual machines")

    def test_user_group_collects_template_groups(self):
        ctx = Context().load(str(TESTS / "test_user_group.decree.yml"))
        ctx.get_template_group("Test Template")

    def test_add_user_collects_groups(self):
        ctx = Context().load(str(TESTS / "test_add_user.yml"))
        ctx.get_user_group("Templar Users")


class TestSetMacro:
    def test_macro_names(self):
        ctx = Context().load(str(TESTS / "test_set_macro.yml"))
        ctx.get_macro("{$SNMP_COMMUNITY}")
        ctx.get_macro("{$DB_PASSWORD}")


class TestMultipleLoads:
    def test_accumulates(self):
        ctx = Context()
        ctx.load(str(TESTS / "reference_templates.yml"))
        ctx.load(str(TESTS / "reference_hosts.yml"))
        ctx.load(str(TESTS / "test_set_macro.yml"))
        ctx.load(str(TESTS / "test_user_group.decree.yml"))
        ctx.get_template_group("Templar Templates")
        ctx.get_template_group("Test Template")
        ctx.get_host_group("Linux servers")
        ctx.get_host_group("Templar Hosts")
        ctx.get_host_group("Virtual machines")
        ctx.get_user_group("Templar Users")
        ctx.get_macro("{$MY_MACRO}")
        ctx.get_macro("{$SNMP_COMMUNITY}")

    def test_chaining(self):
        ctx = (Context()
               .load(str(TESTS / "reference_templates.yml"))
               .load(str(TESTS / "test_user_group.decree.yml")))
        ctx.get_template_group("Templar Templates")
        ctx.get_template_group("Test Template")
        ctx.get_user_group("Templar Users")


class TestUnknownFormat:
    def test_scroll_rejected(self):
        with pytest.raises(ValueError, match="unknown format"):
            Context().load(str(TESTS / "test_scroll.yml"))

    def test_error_shows_keys(self):
        with pytest.raises(ValueError, match="stages"):
            Context().load(str(TESTS / "test_scroll.yml"))