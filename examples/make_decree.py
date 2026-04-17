from zbxtemplar.modules import DecreeModule
from zbxtemplar.decree import Token, UserMedia, MediaType, UserRole, GuiAccess, Permission, Severity
from zbxtemplar.decree.action_conditions import HostGroupCondition, HostTemplateCondition, HostMetadataCondition


class SampleDecree(DecreeModule):
    def __init__(self, alert_email: str = "alerts@example.com", admin_slack: str = ""):
        super().__init__()

        test_host_group = self.context.get_host_group("Templar Hosts")
        test_template = self.context.get_template("Test Template")

        ops_group = self.add_user_group("Templar Users", gui_access=GuiAccess.INTERNAL)
        ops_group.add_host_group("Linux servers", Permission.NONE)
        ops_group.add_host_group("Virtual machines", Permission.READ)
        ops_group.add_template_group(self.context.get_template_group("Templar Templates"), Permission.READ_WRITE)
        ops_group.add_host_group(test_host_group, Permission.READ)

        admin = self.add_user("zbx-admin", role=UserRole.SUPER_ADMIN)
        admin.set_password("${ZBX_ADMIN_PASSWORD}")
        admin.add_group(ops_group)
        email_media = UserMedia(MediaType.EMAIL, alert_email)
        email_media.set_severity([Severity.AVERAGE, Severity.HIGH, Severity.DISASTER])
        admin.add_media(email_media)
        admin.add_media(UserMedia(MediaType.SLACK, admin_slack))

        service = self.add_user("zbx-service", role=UserRole.USER)
        service.set_password("${ZBX_SERVICE_PASSWORD}")
        service.add_group(ops_group)
        service.set_token(
            Token("monitoring-ro", store_at=".secrets/monitoring-ro.token", expires_at=Token.NEVER),
            force=True
        )
        service_slack = UserMedia(MediaType.SLACK, self.get_macro("TEMPLAR_GLOBAL_MACRO").value)
        service.add_media(service_slack)

        test_action = self.add_trigger_action("Test Action")
        test_action.operations.send_message(groups=[ops_group], message="Test message")
        test_action.recovery_operations.send_message(groups=[ops_group], message="Resolved")
        test_action.update_operations.send_message(groups=[ops_group], message="Acknowledged")
        group_condition = HostGroupCondition(test_host_group)
        template_condition = HostTemplateCondition(test_template)
        test_action.set_conditions(group_condition | template_condition)

        test_registration = self.add_autoregistration_action("Test Registration")
        test_registration.operations.add_host()
        test_registration.operations.link_template(test_template)
        test_registration.set_conditions(HostMetadataCondition("test", HostMetadataCondition.Op.CONTAINS))

        self.set_encryption_defaults(connect_unencrypted=True)
        host_encryption = self.add_host_encryption(
            self.context.get_host("Templar Host"),
            accept_unencrypted=True,
        )
        host_encryption.set_psk(identity="zbxtemplar_psk", psk="${ZBX_ENCRYPTED_PSK}")


if __name__ == "__main__":
    import yaml

    module = SampleDecree()
    print(yaml.dump(module.to_export(), default_flow_style=False, sort_keys=False))
