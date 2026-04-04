class ExecutorError(Exception):
    """Base class for execution failures."""
    pass

class ExecutorApiError(ExecutorError):
    """API request failures during execution, typically wrapping Zabbix API exceptions."""
    pass

class ExecutorParseError(ExecutorError):
    """Failed to parse or load input configurations, such as YAML files."""
    def __init__(self, message, path=None):
        super().__init__(message)
        self.path = path
