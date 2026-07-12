"""Demostración de aceptación de la Data Quality Layer (IT-019-002).

El script usa exclusivamente la API pública:

- `MarketData`
- `MarketDataQualityChecker`
- `QualityReport`

Genera dos datasets sintéticos (válido / inválido), ejecuta la comprobación
de calidad y realiza las verificaciones explícitas solicitadas.
"""

from datetime import datetime

from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker, QualityReport


def _dt(date_str: str) -> datetime:
    return datetime.fromisoformat(date_str)


def build_valid_market_data() -> list[MarketData]:
    # Ordered, no duplicates, OHLC valid, positive volume
    return [
        MarketData("AAPL", _dt("2024-01-02"), 130.0, 132.0, 129.0, 131.0, 1_000_000),
        MarketData("AAPL", _dt("2024-01-03"), 131.0, 133.0, 130.0, 132.0, 1_200_000),
        MarketData("AAPL", _dt("2024-01-04"), 132.0, 134.0, 131.0, 133.0, 1_100_000),
    ]


def build_invalid_market_data() -> list[MarketData]:
    # Introduce: duplicate timestamp and OHLC inconsistency (high < close)
    t1 = _dt("2024-01-02")
    t2 = _dt("2024-01-03")
    return [
        MarketData("AAPL", t1, 130.0, 132.0, 129.0, 131.0, 1_000_000),
        MarketData("AAPL", t2, 131.0, 133.0, 130.0, 132.0, 1_200_000),
        MarketData("AAPL", t2, 131.0, 133.0, 130.0, 132.0, 1_200_000),  # duplicate
        # OHLC inconsistency: single OHLC error (high lower than open)
        MarketData("AAPL", _dt("2024-01-04"), 130.0, 129.0, 128.0, 128.5, 1_100_000),
    ]


def _print_valid_summary(report: QualityReport) -> None:
    print("--- Caso VÁLIDO ---")
    print(f"Nombre del dataset: {report.dataset_id}")
    print(f"Número de registros: {report.total_records}")
    print(f"Status: {report.status}")
    print(f"Número de errores: {len(report.validation_errors)}")
    print()


def _print_invalid_summary(report: QualityReport) -> None:
    print("--- Caso INVÁLIDO ---")
    print(f"Nombre del dataset: {report.dataset_id}")
    print(f"Número de registros: {report.total_records}")
    print(f"Status: {report.status}")
    print(f"Número de duplicados: {report.duplicate_records}")
    print(f"Número de errores: {len(report.validation_errors)}")
    print("Lista de errores detectados:")
    for e in report.validation_errors:
        print(f" - {e}")
    print()





def main() -> None:
    # Encabezado institucional
    print("==========================================")
    print("TramitaGO Quant Platform")
    print("Data Quality Acceptance Demonstration IT-019-002")
    print("==========================================")
    print("MarketData -> MarketDataQualityChecker -> QualityReport")
    print()

    checker = MarketDataQualityChecker()

    valid = build_valid_market_data()
    invalid = build_invalid_market_data()

    valid_report = checker.check(valid, dataset_id="valid_market_data")
    invalid_report = checker.check(invalid, dataset_id="invalid_market_data")

    # Verificaciones obligatorias
    assert isinstance(valid_report, QualityReport), "valid_report debe ser QualityReport"
    assert isinstance(invalid_report, QualityReport), "invalid_report debe ser QualityReport"

    assert valid_report.status == "PASS", "Dataset válido debe tener status PASS"
    assert invalid_report.status == "FAIL", "Dataset inválido debe tener status FAIL"

    # Errores esperados: duplicado e inconsistencia OHLC
    assert any("duplicates symbol" in e for e in invalid_report.validation_errors), (
        "Se esperaba error de duplicado en el dataset inválido"
    )

    ohlc_errors = [
        e
        for e in invalid_report.validation_errors
        if "high" in e or "low" in e
    ]
    assert len(ohlc_errors) >= 1, "Se esperaba al menos 1 error OHLC en el dataset inválido"

    # Mostrar resultados mínimos solicitados
    _print_valid_summary(valid_report)
    _print_invalid_summary(invalid_report)


if __name__ == "__main__":
    main()
