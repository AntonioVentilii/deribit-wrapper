class DeribitClientWarning(Warning):
    pass


class InvalidMarginModelError(Exception):
    pass






class WaitRequiredError(Exception):
    pass







class PriceUnavailableError(Exception):
    pass


class RequestError(Exception):
    pass


class ServiceUnavailable(RequestError):
    pass


class InvalidParameterForRequest(RequestError):
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
