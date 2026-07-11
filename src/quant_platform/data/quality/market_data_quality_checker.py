"""MarketData quality checker.

Responsibility:
    Evaluate basic quality conditions for provider-independent MarketData.

Inputs:
    A list of MarketData records.

Outputs:
    QualityReport with counters, errors, and status.
"""

from collections.abc import Sequence
from datetime import datetime
from math import isfinite
from numbers import Real

from quant_platform.data.models import MarketData
from quant_platform.data.quality.quality_report import QualityReport

PASS_STATUS = "PASS"
FAIL_STATUS = "FAIL"
INVALID_INPUT_MESSAGE = "Expected a sequence of MarketData records."


class MarketDataQualityChecker:
    """Evaluate MVP quality rules for MarketData records."""

    def check(
        self,
        records: Sequence[MarketData],
        dataset_id: str = "market_data",
    ) -> QualityReport:
        """Return an explainable quality report without mutating records."""
        if isinstance(records, (str, bytes)):
            raise TypeError(INVALID_INPUT_MESSAGE)

        market_records = list(records)
        validation_errors: list[str] = []

        if not market_records:
            validation_errors.append("Dataset is empty.")
            return QualityReport(
                dataset_id=dataset_id,
                total_records=0,
                missing_records=0,
                duplicate_records=0,
                validation_errors=validation_errors,
                status=FAIL_STATUS,
            )

        if not all(isinstance(record, MarketData) for record in market_records):
            raise TypeError(INVALID_INPUT_MESSAGE)

        missing_records = 0
        duplicate_records = 0
        seen_keys: set[tuple[str, datetime]] = set()
        previous_timestamp_by_symbol: dict[str, datetime] = {}

        for index, record in enumerate(market_records):
            record_has_missing_value = self._has_missing_value(record)
            if record_has_missing_value:
                missing_records += 1
                validation_errors.append(f"Record {index} has missing values.")

            if not record.symbol.strip():
                validation_errors.append(f"Record {index} has an invalid symbol.")

            key = (record.symbol, record.timestamp)
            if key in seen_keys:
                duplicate_records += 1
                validation_errors.append(
                    "Record "
                    f"{index} duplicates symbol {record.symbol} "
                    f"at timestamp {record.timestamp.isoformat()}."
                )
            else:
                seen_keys.add(key)

            previous_timestamp = previous_timestamp_by_symbol.get(record.symbol)
            if previous_timestamp is not None and record.timestamp < previous_timestamp:
                validation_errors.append(
                    "Record "
                    f"{index} timestamp is out of order for symbol {record.symbol}."
                )
            previous_timestamp_by_symbol[record.symbol] = record.timestamp

            self._add_numeric_errors(record, index, validation_errors)
            self._add_ohlc_errors(record, index, validation_errors)

        status = FAIL_STATUS if validation_errors else PASS_STATUS
        return QualityReport(
            dataset_id=dataset_id,
            total_records=len(market_records),
            missing_records=missing_records,
            duplicate_records=duplicate_records,
            validation_errors=validation_errors,
            status=status,
        )

    def _has_missing_value(self, record: MarketData) -> bool:
        values = (
            record.symbol,
            record.timestamp,
            record.open,
            record.high,
            record.low,
            record.close,
            record.volume,
        )
        return any(value is None for value in values)

    def _add_numeric_errors(
        self,
        record: MarketData,
        index: int,
        validation_errors: list[str],
    ) -> None:
        numeric_fields = {
            "open": record.open,
            "high": record.high,
            "low": record.low,
            "close": record.close,
            "volume": record.volume,
        }

        for field_name, value in numeric_fields.items():
            if not isinstance(value, Real) or not isfinite(float(value)):
                validation_errors.append(f"Record {index} has invalid {field_name}.")
                continue

            if field_name != "volume" and value <= 0:
                validation_errors.append(f"Record {index} has impossible {field_name}.")

            if field_name == "volume" and value < 0:
                validation_errors.append(f"Record {index} has impossible volume.")

    def _add_ohlc_errors(
        self,
        record: MarketData,
        index: int,
        validation_errors: list[str],
    ) -> None:
        ohlc_values = (record.open, record.high, record.low, record.close)
        if not all(
            isinstance(value, Real) and isfinite(float(value)) for value in ohlc_values
        ):
            return

        if record.high < record.open:
            validation_errors.append(f"Record {index} has high lower than open.")
        if record.high < record.close:
            validation_errors.append(f"Record {index} has high lower than close.")
        if record.low > record.open:
            validation_errors.append(f"Record {index} has low greater than open.")
        if record.low > record.close:
            validation_errors.append(f"Record {index} has low greater than close.")
