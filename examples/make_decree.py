from zbxtemplar.core import DecreeModule
from zbxtemplar.core.constants import MediaType, UserRole
from zbxtemplar.core.DecreeEntity import UserGroup, User


class SampleDecree(DecreeModule):
    def __init__(self, alert_email: str = "alerts@example.com"):
        super().__init__()

        ops_group = UserGroup("Operations", gui_access="INTERNAL")
        ops_group.add_host_group("Linux servers", "READ")
        ops_group.add_host_group("Virtual machines", "READ_WRITE")
        ops_group.add_template_group("Templar Templates", "READ_WRITE")
        self.add_user_group(ops_group)

        viewers_group = UserGroup("Viewers")
        viewers_group.add_host_group("Linux servers", "READ")
        viewers_group.add_template_group("Templar Templates", "READ")
        self.add_user_group(viewers_group)

        admin = User("zbx-admin", role=UserRole.SUPER_ADMIN)
        admin.set_password("${ZBX_ADMIN_PASSWORD}")
        admin.add_group(ops_group)
        admin.add_media(MediaType.EMAIL, alert_email, severity="AVERAGE,HIGH,DISASTER")
        admin.add_media(MediaType.SLACK, "#ops-alerts")
        self.add_user(admin)

        service = User("zbx-service", role=UserRole.USER)
        service.set_password("${ZBX_SERVICE_PASSWORD}")
        service.add_group(viewers_group)
        service.set_token("monitoring-ro", force=True)
        self.add_user(service)


if __name__ == "__main__":
    import yaml

    module = SampleDecree()
    print(yaml.dump(module.to_export(), default_flow_style=False, sort_keys=False))