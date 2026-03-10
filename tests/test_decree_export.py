from pathlib import Path

import pytest
import yaml

from zbxtemplar.core import DecreeModule, Context
from zbxtemplar.core.constants import MediaType, UserRole, GuiAccess, Permission, Severity
from zbxtemplar.core.DecreeEntity import UserGroup, User, UserMedia

TESTS = Path(__file__).parent


class SampleDecree(DecreeModule):
    def __init__(self, context=None):
        super().__init__(context=context)

        ops_group = UserGroup("Templar Users", gui_access=GuiAccess.INTERNAL)
        ops_group.add_host_group("Linux servers", Permission.NONE)
        ops_group.add_host_group("Virtual machines", Permission.READ)
        ops_group.add_host_group(context.get_host_group("Templar Hosts"), Permission.READ)
        ops_group.add_template_group(context.get_template_group("Templar Templates"), Permission.READ_WRITE)
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
        service.set_token("monitoring-ro", force=True)
        self.add_user(service)


def _load_context():
    return (Context()
            .load(str(TESTS / "reference_templates.yml"))
            .load(str(TESTS / "reference_hosts.yml")))


def test_decree_matches_reference():
    ctx = _load_context()
    module = SampleDecree(context=ctx)
    export = module.to_export()

    with open(TESTS / "reference_decree.yml") as f:
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