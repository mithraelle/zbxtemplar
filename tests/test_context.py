from pathlib import Path

import pytest

from zbxtemplar.core import Context

TESTS = Path(__file__).parent


class TestZabbixExport:
    def test_template_groups(self):
        ctx = Context().load(str(TESTS / "reference_templates.yml"))
        assert ctx.template_group_names == {"Templar Templates"}

    def test_host_groups(self):
        ctx = Context().load(str(TESTS / "reference_hosts.yml"))
        assert ctx.host_group_names == {"Templar Hosts"}

    def test_macros_from_templates(self):
        ctx = Context().load(str(TESTS / "reference_templates.yml"))
        assert "{$MY_MACRO}" in ctx.macro_names

    def test_macros_from_hosts(self):
        ctx = Context().load(str(TESTS / "reference_hosts.yml"))
        assert "{$MY_HOST_MACRO}" in ctx.macro_names

    def test_combined_file(self):
        ctx = Context().load(str(TESTS / "reference_combined.yml"))
        assert ctx.template_group_names == {"Templar Templates"}
        assert ctx.host_group_names == {"Templar Hosts"}
        assert "{$MY_MACRO}" in ctx.macro_names
        assert "{$MY_HOST_MACRO}" in ctx.macro_names


class TestDecree:
    def test_user_group(self):
        ctx = Context().load(str(TESTS / "test_user_group.decree.yml"))
        assert ctx.user_group_names == {"Templar Users"}

    def test_user_group_collects_host_groups(self):
        ctx = Context().load(str(TESTS / "test_user_group.decree.yml"))
        assert ctx.host_group_names == {"Linux servers", "Virtual machines"}

    def test_user_group_collects_template_groups(self):
        ctx = Context().load(str(TESTS / "test_user_group.decree.yml"))
        assert ctx.template_group_names == {"Test Template"}

    def test_add_user_collects_groups(self):
        ctx = Context().load(str(TESTS / "test_add_user.yml"))
        assert "Templar Users" in ctx.user_group_names


class TestSetMacro:
    def test_macro_names(self):
        ctx = Context().load(str(TESTS / "test_set_macro.yml"))
        assert ctx.macro_names == {"{$SNMP_COMMUNITY}", "{$DB_PASSWORD}"}


class TestMultipleLoads:
    def test_accumulates(self):
        ctx = Context()
        ctx.load(str(TESTS / "reference_templates.yml"))
        ctx.load(str(TESTS / "reference_hosts.yml"))
        ctx.load(str(TESTS / "test_set_macro.yml"))
        ctx.load(str(TESTS / "test_user_group.decree.yml"))
        assert ctx.template_group_names == {"Templar Templates", "Test Template"}
        assert ctx.host_group_names == {"Linux servers", "Templar Hosts", "Virtual machines"}
        assert ctx.user_group_names == {"Templar Users"}
        assert "{$MY_MACRO}" in ctx.macro_names
        assert "{$SNMP_COMMUNITY}" in ctx.macro_names

    def test_chaining(self):
        ctx = (Context()
               .load(str(TESTS / "reference_templates.yml"))
               .load(str(TESTS / "test_user_group.decree.yml")))
        assert ctx.template_group_names == {"Templar Templates", "Test Template"}
        assert ctx.user_group_names == {"Templar Users"}


class TestUnknownFormat:
    def test_scroll_rejected(self):
        with pytest.raises(ValueError, match="unknown format"):
            Context().load(str(TESTS / "test_scroll.yml"))

    def test_error_shows_keys(self):
        with pytest.raises(ValueError, match="stages"):
            Context().load(str(TESTS / "test_scroll.yml"))