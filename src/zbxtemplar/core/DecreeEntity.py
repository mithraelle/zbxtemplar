def _validate(value, allowed, label):
    if value not in allowed:
        raise ValueError(f"Invalid {label} '{value}', expected one of: {', '.join(allowed)}")


class DecreeEntity:
    def to_dict(self) -> dict:
        result = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            if value is None or value == {} or value == []:
                continue
            list_method = getattr(self, f'{key}_to_list', None)
            if list_method:
                items = list_method()
                if items:
                    result[key] = items
            else:
                result[key] = value
        return result