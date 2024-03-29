class TokenExtendedException(Exception):
    """
    Base except which all sanic_jwt_extended errors extend
    """

    ...


class InvalidHeaderError(TokenExtendedException):
    """
    An error getting header information from a request
    """

    ...


class NoAuthorizationError(TokenExtendedException):
    """
    An error raised when no authorization token was found in a protected endpoint
    """

    ...


class AccessDeniedError(TokenExtendedException):
    """
    Error raised when a valid JWT attempt to access an endpoint
    protected by jwt_required with not allowed role
    """

    ...


class ConfigurationConflictError(TokenExtendedException):
    """
    Error raised when trying to use allow and deny option together in jwt_required
    """

    ...


class CSRFError(TokenExtendedException):
    ...
