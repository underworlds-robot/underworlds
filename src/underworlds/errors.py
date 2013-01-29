class UnderworldsError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class TimeoutError(UnderworldsError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

