"""Enki API exceptions."""


class EnkiError(Exception):
    """Base Enki error."""


class EnkiAuthError(EnkiError):
    """Invalid credentials or expired session."""


class EnkiConnectionError(EnkiError):
    """Network or upstream API failure."""
