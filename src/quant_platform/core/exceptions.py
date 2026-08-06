"""Structural errors for neutral reference identity contracts."""


class ReferenceIdentityError(ValueError):
    """Base error for an invalid reference identity."""


class InvalidInstrumentReferenceError(ReferenceIdentityError):
    """Raised when an instrument reference is structurally invalid."""


class InvalidCurrencyReferenceError(ReferenceIdentityError):
    """Raised when a currency reference is structurally invalid."""


__all__ = [
    "InvalidCurrencyReferenceError",
    "InvalidInstrumentReferenceError",
    "ReferenceIdentityError",
]
