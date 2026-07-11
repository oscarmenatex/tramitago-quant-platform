"""Run the Data Quality Foundation MVP demonstration."""

from datetime import datetime

from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker, QualityReport


def build_market_data() -> list[MarketData]:
    """Build deterministic MarketData records for the demonstration."""
    return [
        MarketData(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 2),
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=1_000_000.0,
        ),
        MarketData(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 3),
            open=104.0,
            high=107.0,
            low=103.0,
            close=106.0,
            volume=1_200_000.0,
        ),
        MarketData(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 3),
            open=106.0,
            high=105.0,
            low=104.0,
            close=107.0,
            volume=950_000.0,
        ),
    ]


def print_report(report: QualityReport) -> None:
    """Print the minimum explainable quality report summary."""
    print(f"Dataset: {report.dataset_id}")
    print(f"Cantidad de registros: {report.total_records}")
    print(f"Registros faltantes: {report.missing_records}")
    print(f"Registros duplicados: {report.duplicate_records}")
    print(f"Estado: {report.status}")
    print("Errores encontrados:")

    if not report.validation_errors:
        print("- Ninguno")
        return

    for error in report.validation_errors:
        print(f"- {error}")


def main() -> None:
    print("==========================================")
    print("TramitaGO Quant Platform")
    print("Data Quality Foundation MVP Demonstration")
    print("==========================================")
    print("MarketData -> MarketDataQualityChecker -> QualityReport")

    records = build_market_data()
    checker = MarketDataQualityChecker()
    report = checker.check(records, dataset_id="demo_market_data")

    print_report(report)


if __name__ == "__main__":
    main()
