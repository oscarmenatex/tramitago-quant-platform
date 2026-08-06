"""Immutable neutral reference identity contracts."""

from dataclasses import dataclass
from hashlib import sha256
import json

from .exceptions import InvalidCurrencyReferenceError, InvalidInstrumentReferenceError


def _identity_for(contract: str, components: tuple[str, ...]) -> str:
    canonical = json.dumps(
        {"components": components, "contract": contract},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_text(value: object, label: str, error_type: type[ValueError]) -> str:
    if not isinstance(value, str):
        raise error_type(f"{label} must be a string.")
    if not value:
        raise error_type(f"{label} must not be empty.")
    if value != value.strip():
        raise error_type(f"{label} must not contain peripheral whitespace.")
    return value


@dataclass(frozen=True, slots=True, eq=False)
class InstrumentReference:
    """A canonical public identity for an instrument."""

    identification_scheme: str
    identification_value: str

    def __post_init__(self) -> None:
        scheme = _validate_text(
            self.identification_scheme,
            "Identification scheme",
            InvalidInstrumentReferenceError,
        )
        value = _validate_text(
            self.identification_value,
            "Identification value",
            InvalidInstrumentReferenceError,
        )
        object.__setattr__(self, "identification_scheme", scheme.upper())
        object.__setattr__(self, "identification_value", value)

    @property
    def semantic_identity(self) -> str:
        """Return the stable identity derived from the canonical components."""
        return _identity_for(
            type(self).__name__,
            (self.identification_scheme, self.identification_value),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, InstrumentReference):
            return NotImplemented
        return self._identity_components == other._identity_components

    def __hash__(self) -> int:
        return hash(self._identity_components)

    @property
    def _identity_components(self) -> tuple[str, str]:
        return self.identification_scheme, self.identification_value


@dataclass(frozen=True, slots=True, eq=False)
class CurrencyReference:
    """A canonical public identity for a currency."""

    currency_code: str

    def __post_init__(self) -> None:
        code = _validate_text(
            self.currency_code,
            "Currency code",
            InvalidCurrencyReferenceError,
        )
        if len(code) != 3 or not code.isascii() or not code.isalpha():
            raise InvalidCurrencyReferenceError(
                "Currency code must contain exactly three ASCII letters."
            )
        object.__setattr__(self, "currency_code", code.upper())

    @property
    def semantic_identity(self) -> str:
        """Return the stable identity derived from the canonical code."""
        return _identity_for(type(self).__name__, (self.currency_code,))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CurrencyReference):
            return NotImplemented
        return self.currency_code == other.currency_code

    def __hash__(self) -> int:
        return hash(self.currency_code)
