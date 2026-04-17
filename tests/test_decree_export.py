import pytest
import yaml

from zbxtemplar.modules import DecreeModule, Context
from zbxtemplar.decree import Token, UserGroup, User, UserMedia, MediaType, UserRole, GuiAccess, Permission, Severity
from zbxtemplar.decree.Action import TriggerAction, AutoregistrationAction
from zbxtemplar.decree.action_conditions import HostGroupCondition, HostTemplateCondition, HostMetadataCondition
from tests.paths import REFERENCE_DIR


class SampleDecree(DecreeModule):
    def __init__(self):
        super().__init__()

        test_host_group = self.context.get_host_group("Templar Hosts")
        test_template = self.context.get_template("Test Template")

        ops_group = UserGroup("Templar Users", gui_access=GuiAccess.INTERNAL)
        ops_group.add_host_group("Linux servers", Permission.NONE)
        ops_group.add_host_group("Virtual machines", Permission.READ)
        ops_group.add_host_group(test_host_group, Permission.READ)
        ops_group.add_template_group(self.context.get_template_group("Templar Templates"), Permission.READ_WRITE)
        self.add_user_group(ops_group)

        admin = User("zbx-admin", role=UserRole.SUPER_ADMIN)
        admin.set_password("${ZBX_ADMIN_PASSWORD}")
        admin.add_group(ops_group)
        email_media = UserMedia(MediaType.EMAIL, "alerts@example.com")
        email_media.set_severity([Severity.AVERAGE, Severity.HIGH, Severity.DISASTER])
        admin.add_media(email_media)
        admin.add_media(UserMedia(MediaType.SLACK, "#ops-alerts"))
        self.add_user(admin)

        service = User("zbx-service", role=UserRole.USER)
        service.set_password("${ZBX_SERVICE_PASSWORD}")
        service.add_group(ops_group)
        service.set_token(
            Token(
                "monitoring-ro",
                expires_at=Token.NEVER,
                store_at=".secrets/monitoring-ro.token",
            ),
            force=True,
        )
        self.add_user(service)

        action = TriggerAction("Test Action")
        action.operations.send_message(groups=[ops_group], message="Test message")
        action.set_conditions(
            HostGroupCondition(test_host_group) | HostTemplateCondition(test_template)
        )
        self.add_action(action)

        reg = AutoregistrationAction("Test Registration")
        reg.operations.add_host()
        reg.operations.link_template(test_template)
        reg.set_conditions(HostMetadataCondition("test", HostMetadataCondition.Op.CONTAINS))
        self.add_action(reg)


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
        group.add_template_group(ctx.get_template_group("Nonexistent"), Permission.READ)


def test_context_rejects_missing_host_group():
    ctx = _load_context()
    with pytest.raises(ValueError, match="not found in context"):
        group = UserGroup("Bad")
        group.add_host_group(ctx.get_host_group("Nonexistent"), Permission.READ)


def test_token_init_requires_store_at():
    with pytest.raises(ValueError, match="token.store_at must be a file path"):
        Token("api-reader-token", store_at=None, expires_at=Token.NEVER)
