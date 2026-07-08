"""Run the Data Layer acceptance demonstration."""

from quant_platform.data import DataLoader
from quant_platform.data.models import MarketData

PROVIDER_NAME = "yahoo"
SYMBOL = "AAPL"
START_DATE = "2024-01-01"
END_DATE = "2025-01-01"
INTERVAL = "1d"


def _ensure_no_dataframe_exposed(records: object) -> None:
    if type(records).__name__ == "DataFrame":
        raise TypeError("Data Layer exposed a DataFrame to the consumer.")

    if isinstance(records, list) and any(
        type(record).__name__ == "DataFrame" for record in records
    ):
        raise TypeError("Data Layer exposed a DataFrame inside the result list.")


def _validate_contract(records: object) -> list[MarketData]:
    _ensure_no_dataframe_exposed(records)

    if not isinstance(records, list):
        raise TypeError(
            "Data Layer returned an invalid type: "
            f"expected list, got {type(records).__name__}."
        )

    if not records:
        raise ValueError("Data Layer returned no market data records.")

    if not all(isinstance(record, MarketData) for record in records):
        raise TypeError("Data Layer returned non-MarketData records.")

    return records


def main() -> None:
    print("==========================================")
    print("TramitaGO Quant Platform")
    print("Data Layer Acceptance Demonstration")
    print("==========================================")

    data_loader = DataLoader(data_provider=PROVIDER_NAME)
    records = _validate_contract(
        data_loader.get_historical_data(
            symbol=SYMBOL,
            start_date=START_DATE,
            end_date=END_DATE,
            interval=INTERVAL,
        )
    )

    print(f"Provider utilizado: {PROVIDER_NAME}")
    print(f"Simbolo: {SYMBOL}")
    print(f"Periodo solicitado: {START_DATE} a {END_DATE}")
    print(f"Intervalo: {INTERVAL}")
    print(f"Numero de registros obtenidos: {len(records)}")
    print(f"Primer registro: {records[0]}")
    print(f"Ultimo registro: {records[-1]}")
    print(f"Tipo del objeto devuelto: {type(records).__name__}")
    print("Estado final: PASS")


if __name__ == "__main__":
    main()
