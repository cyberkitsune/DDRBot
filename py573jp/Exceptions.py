class EALinkException(Exception):
    jscontext = None

    def __init__(self, message, jscontext=None):
        Exception.__init__(self, message)
        self.jscontext = jscontext


class EALoginException(EALinkException):
    pass


class EAMaintenanceException(EALinkException):
    pass
