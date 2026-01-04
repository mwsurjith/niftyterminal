"""Custom exceptions for Nifty Terminal."""


class NiftyTerminalError(Exception):
    """Base exception for all Nifty Terminal errors."""

    pass


class SessionError(NiftyTerminalError):
    """Raised when session creation or warmup fails."""

    pass


class APIError(NiftyTerminalError):
    """Raised when an API request fails."""

    pass
