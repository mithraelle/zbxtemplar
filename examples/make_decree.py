from aiohttp.helpers import set_exception
from packaging.metadata import Metadata

from zbxtemplar.core import DecreeModule
from zbxtemplar.decree import Token, UserGroup, User, UserMedia, MediaType, UserRole, GuiAccess, Permission, Severity
from zbxtemplar.decree.Action import TriggerAction, AutoregistrationAction
from zbxtemplar.decree.action_conditions import HostGroupCondition, HostTemplateCondition, HostMetadataCondition
from zbxtemplar.decree.Encryption import HostEncryption, Encryption


class SampleDecree(DecreeModule):
    def __init__(self, context=None, alert_email: str = "alerts@example.com", admin_slack: str = ""):
        super().__init__(context=context)

        test_host_group = context.get_host_group("Templar Hosts")
        test_template = context.get_template("Test Template")

        ops_group = UserGroup("Templar Users", gui_access=GuiAccess.INTERNAL)
        ops_group.add_host_group("Linux servers", Permission.NONE)
        ops_group.add_host_group("Virtual machines", Permission.READ)
        ops_group.add_template_group(context.get_template_group("Templar Templates"), Permission.READ_WRITE)
        ops_group.add_host_group(test_host_group, Permission.READ)
        self.add_user_group(ops_group)


        admin = User("zbx-admin", role=UserRole.SUPER_ADMIN)
        admin.set_password("${ZBX_ADMIN_PASSWORD}")
        admin.add_group(ops_group)
        email_media = UserMedia(MediaType.EMAIL, alert_email)
        email_media.set_severity([Severity.AVERAGE, Severity.HIGH, Severity.DISASTER])
        admin.add_media(email_media)
        admin.add_media(UserMedia(MediaType.SLACK, admin_slack))
        self.add_user(admin)

        service = User("zbx-service", role=UserRole.USER)
        service.set_password("${ZBX_SERVICE_PASSWORD}")
        service.add_group(ops_group)
        service.set_token(
            Token("monitoring-ro", store_at=".secrets/monitoring-ro.token", expires_at=Token.NEVER),
            force=True
        )
        self.add_user(service)

        test_action = TriggerAction("Test Action")
        test_action.operations.send_message(groups=[ops_group], message="Test message")
        self.add_action(test_action)
        group_condition = HostGroupCondition(test_host_group)
        template_condition = HostTemplateCondition(test_template)
        test_action.set_conditions(group_condition | template_condition)

        test_registration = AutoregistrationAction("Test Registration")
        test_registration.operations.add_host()
        test_registration.operations.link_template(test_template)
        test_registration.set_conditions(HostMetadataCondition("test", HostMetadataCondition.Op.CONTAINS))
        self.add_action(test_registration)

        self.set_encryption_defaults(Encryption(connect_unencrypted=True))
        host_encryption = Encryption(accept_unencrypted=True)
        host_encryption.set_psk(identity="zbxtemplar_psk", psk="${ZBX_ENCRYPTED_PSK}")
        self.add_host_encryption(context.get_host("Templar Host"), host_encryption)


if __name__ == "__main__":
    import yaml

    module = SampleDecree()
    print(yaml.dump(module.to_export(), default_flow_style=False, sort_keys=False))
