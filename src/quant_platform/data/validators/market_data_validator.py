"""MarketData integrity validator.

Responsibility:
    Accept or reject normalized market data before platform consumption.

Inputs:
    A sequence of MarketData records.

Outputs:
    list[MarketData] when valid, or ValueError when invalid.
"""

from collections.abc import Sequence
from datetime import datetime
from math import isfinite
from numbers import Real

from quant_platform.data.models import MarketData


class MarketDataValidator:
    """Validate the minimum integrity rules for MarketData records."""

    def validate(self, records: Sequence[MarketData]) -> list[MarketData]:
        """Validate all records and return them as a list."""
        validated_records = list(records)
        if not validated_records:
            raise ValueError("Market data cannot be empty.")

        for index, record in enumerate(validated_records):
            self._validate_record(record, index)

        return validated_records

    def _validate_record(self, record: MarketData, index: int) -> None:
        if not isinstance(record, MarketData):
            raise TypeError(f"Record {index} is not a MarketData instance.")

        if not record.symbol or not record.symbol.strip():
            raise ValueError(f"Record {index} has an invalid symbol.")

        if not isinstance(record.timestamp, datetime):
            raise ValueError(f"Record {index} has an invalid timestamp.")

        numeric_fields = {
            "open": record.open,
            "high": record.high,
            "low": record.low,
            "close": record.close,
            "volume": record.volume,
        }
        for field_name, value in numeric_fields.items():
            if not isinstance(value, Real) or not isfinite(float(value)):
                raise ValueError(f"Record {index} has invalid {field_name}.")

        if record.volume < 0:
            raise ValueError(f"Record {index} has negative volume.")

        if record.high < max(record.open, record.low, record.close):
            raise ValueError(f"Record {index} has inconsistent OHLC values.")

        if record.low > min(record.open, record.high, record.close):
            raise ValueError(f"Record {index} has inconsistent OHLC values.")
