class BotIsNotRunningError(Exception):
    def __init__(self, message):
        super().__init__(message)


class BotModeIsNotConfiguredError(Exception):
    def __init__(self, message):
        super().__init__(message)


class BotConfigurationError():
    def __init__(self, message):
        super().__init__(message)
