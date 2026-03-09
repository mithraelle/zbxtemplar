class DecreeModule:
    def __init__(self, context=None):
        self.context = context
        self.user_groups = []
        self.users = []

    def add_user_group(self, group):
        if any(g.name == group.name for g in self.user_groups):
            return self
        self.user_groups.append(group)
        return self

    def add_user(self, user):
        if any(u.username == user.username for u in self.users):
            return self
        self.users.append(user)
        return self

    def export_user_groups(self) -> dict:
        if not self.user_groups:
            return {}
        return {"user_group": [g.to_dict() for g in self.user_groups]}

    def export_users(self) -> dict:
        if not self.users:
            return {}
        return {"add_user": [u.to_dict() for u in self.users]}

    def to_export(self) -> dict:
        result = {}
        if self.user_groups:
            result["user_group"] = [g.to_dict() for g in self.user_groups]
        if self.users:
            result["add_user"] = [u.to_dict() for u in self.users]
        return result