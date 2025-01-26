class DeribitClientWarning(Warning):
    pass

class InvalidParameterError(Exception):
    pass


class InvalidMarginModelError(Exception):
    pass


class WaitRequiredError(Exception):
    pass

class PriceUnavailableError(Exception):
    pass


class SubaccountError(Exception):
    pass

class SubaccountNameAlreadyTaken(SubaccountError):
    pass

class SubaccountNameWrongFormat(SubaccountError):
    pass

class SubaccountNotRemovable(SubaccountError):
    pass

class SubaccountAlreadyRemoved(SubaccountError):
    pass