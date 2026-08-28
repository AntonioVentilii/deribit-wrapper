"""Exception and warning types raised by the Deribit wrapper."""


class DeribitClientWarning(Warning):
    """Warn about a client misconfiguration, such as missing credentials."""


class InvalidMarginModelError(Exception):
    """Raise when an unsupported margin model is requested."""


class WaitRequiredError(Exception):
    """Raise when the API demands a wait before retrying an operation."""


class PriceUnavailableError(Exception):
    """Raise when no price is available for an instrument."""


class RequestError(Exception):
    """Raise for a failed or malformed API request."""


class ServiceUnavailable(RequestError):
    """Raise when the API stays unavailable after bounded retries."""


class InvalidParameterForRequest(RequestError):
    """Raise when the API rejects a request parameter."""


class SubaccountError(Exception):
    """Raise for subaccount operation failures."""


class SubaccountNameAlreadyTaken(SubaccountError):
    """Raise when the requested subaccount name is already taken."""


class SubaccountNameWrongFormat(SubaccountError):
    """Raise when the requested subaccount name has an invalid format."""


class SubaccountNotRemovable(SubaccountError):
    """Raise when a subaccount cannot be removed."""


class SubaccountAlreadyRemoved(SubaccountError):
    """Raise when removing a subaccount that is already removed."""
