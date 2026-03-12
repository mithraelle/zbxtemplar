class DecreeModule:
    def __init__(self, context=None):
        self.context = context
        self.user_groups = []
        self.users = []
        self.actions = []

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

    def add_action(self, action):
        if any(a.name == action.name for a in self.actions):
            return self
        self.actions.append(action)
        return self

    def export_user_groups(self) -> dict:
        if not self.user_groups:
            return {}
        return {"user_group": [g.to_dict() for g in self.user_groups]}

    def export_users(self) -> dict:
        if not self.users:
            return {}
        return {"add_user": [u.to_dict() for u in self.users]}

    def export_actions(self) -> dict:
        if not self.actions:
            return {}
        return {"actions": [a.to_dict() for a in self.actions]}

    def to_export(self) -> dict:
        result = {}
        if self.user_groups:
            result["user_group"] = [g.to_dict() for g in self.user_groups]
        if self.users:
            result["add_user"] = [u.to_dict() for u in self.users]
        if self.actions:
            result["actions"] = [a.to_dict() for a in self.actions]
        return result