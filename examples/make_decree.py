from zbxtemplar.core import DecreeModule
from zbxtemplar.core.constants import MediaType, UserRole, GuiAccess, Permission, Severity
from zbxtemplar.core.DecreeEntity import UserGroup, User, UserMedia


class SampleDecree(DecreeModule):
    def __init__(self, context=None, alert_email: str = "alerts@example.com", admin_slack: str = ""):
        super().__init__(context=context)

        ops_group = UserGroup("Templar Users", gui_access=GuiAccess.INTERNAL)
        ops_group.add_host_group("Linux servers", Permission.NONE)
        ops_group.add_host_group("Virtual machines", Permission.READ)
        ops_group.add_template_group(context.get_template_group("Templar Templates"), Permission.READ_WRITE)
        ops_group.add_host_group(context.get_host_group("Templar Hosts"), Permission.READ)
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
        service.set_token("monitoring-ro", force=True)
        self.add_user(service)


if __name__ == "__main__":
    import yaml

    module = SampleDecree()
    print(yaml.dump(module.to_export(), default_flow_style=False, sort_keys=False))