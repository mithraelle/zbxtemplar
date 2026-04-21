import pytest
import yaml

from zbxtemplar.modules import DecreeModule, Context
from zbxtemplar.decree import Token, UserGroup, MediaType, UserRole, GuiAccess, Permission, Severity
from zbxtemplar.decree.action_conditions import HostGroupCondition, HostTemplateCondition, HostMetadataCondition
from tests.paths import REFERENCE_DIR


class SampleDecree(DecreeModule):
    def compose(self):
        test_host_group = self.context.get_host_group("Templar Hosts")
        test_template = self.context.get_template("Test Template")

        ops_group = self.add_user_group("Templar Users", gui_access=GuiAccess.INTERNAL)
        ops_group.link_host_group("Linux servers", Permission.NONE)
        ops_group.link_host_group("Virtual machines", Permission.READ)
        ops_group.link_host_group(test_host_group, Permission.READ)
        ops_group.link_template_group(self.context.get_template_group("Templar Templates"), Permission.READ_WRITE)

        admin = self.add_user("zbx-admin", role=UserRole.SUPER_ADMIN)
        admin.set_password("${ZBX_ADMIN_PASSWORD}")
        admin.link_group(ops_group)
        admin.add_media(MediaType.EMAIL, "alerts@example.com").set_severity(
            [Severity.AVERAGE, Severity.HIGH, Severity.DISASTER]
        )
        admin.add_media(MediaType.SLACK, "#ops-alerts")

        service = self.add_user("zbx-service", role=UserRole.USER)
        service.set_password("${ZBX_SERVICE_PASSWORD}")
        service.link_group(ops_group)
        service.set_token(
            "monitoring-ro",
            expires_at=Token.NEVER,
            store_at=".secrets/monitoring-ro.token",
            force=True,
        )

        action = self.add_trigger_action("Test Action")
        action.operations.send_message(groups=[ops_group], message="Test message")
        action.set_conditions(
            HostGroupCondition(test_host_group) | HostTemplateCondition(test_template)
        )

        reg = self.add_autoregistration_action("Test Registration")
        reg.operations.add_host()
        reg.operations.link_template(test_template)
        reg.set_conditions(HostMetadataCondition("test", HostMetadataCondition.Op.CONTAINS))


def _load_context():
    return (Context()
            .load(str(REFERENCE_DIR / "templates.yml"))
            .load(str(REFERENCE_DIR / "hosts.yml")))


def _make_sample_decree(context):
    SampleDecree.context = context
    return SampleDecree()


def test_decree_matches_reference():
    ctx = _load_context()
    module = _make_sample_decree(ctx)
    export = module.to_export()

    with open(REFERENCE_DIR / "decree.yml") as f:
        expected = yaml.safe_load(f)

    assert export == expected


def test_actions_export_matches_reference():
    ctx = _load_context()
    module = _make_sample_decree(ctx)
    export = module.export_actions()

    with open(REFERENCE_DIR / "actions.yml") as f:
        expected = yaml.safe_load(f)

    assert export == expected


def test_context_rejects_missing_template_group():
    ctx = _load_context()
    with pytest.raises(ValueError, match="not found in context"):
        group = UserGroup("Bad")
        group.link_template_group(ctx.get_template_group("Nonexistent"), Permission.READ)


def test_context_rejects_missing_host_group():
    ctx = _load_context()
    with pytest.raises(ValueError, match="not found in context"):
        group = UserGroup("Bad")
        group.link_host_group(ctx.get_host_group("Nonexistent"), Permission.READ)


def test_token_init_requires_store_at():
    with pytest.raises(ValueError, match="token.store_at must be a file path"):
        Token("api-reader-token", store_at=None, expires_at=Token.NEVER)


class EmptyDecree(DecreeModule):
    def compose(self):
        pass


def test_add_user_group_constructs_and_returns_user_group():
    module = EmptyDecree()

    group = module.add_user_group("Standalone Group", gui_access=GuiAccess.INTERNAL)

    assert group.name == "Standalone Group"
    assert group.gui_access == GuiAccess.INTERNAL
    assert module.user_groups == [group]


def test_add_user_constructs_and_returns_user():
    module = EmptyDecree()

    user = module.add_user("standalone-user", role=UserRole.USER)

    assert user.username == "standalone-user"
    assert user.role == UserRole.USER
    assert module.users == [user]


def test_add_action_helpers_construct_and_return_actions():
    module = EmptyDecree()

    trigger_action = module.add_trigger_action("Standalone Trigger Action")
    autoreg_action = module.add_autoregistration_action("Standalone Registration Action")

    assert trigger_action.name == "Standalone Trigger Action"
    assert autoreg_action.name == "Standalone Registration Action"
    assert module.actions == [trigger_action, autoreg_action]


def test_decree_module_add_helpers_reject_duplicates():
    module = EmptyDecree()

    module.add_user_group("Duplicate Group")
    with pytest.raises(ValueError, match="duplicate user group 'Duplicate Group'"):
        module.add_user_group("Duplicate Group")

    module.add_user("duplicate-user", role=UserRole.USER)
    with pytest.raises(ValueError, match="duplicate user 'duplicate-user'"):
        module.add_user("duplicate-user", role=UserRole.ADMIN)

    module.add_trigger_action("Duplicate Action")
    with pytest.raises(ValueError, match="duplicate action 'Duplicate Action'"):
        module.add_autoregistration_action("Duplicate Action")
