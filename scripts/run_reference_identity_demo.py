from quant_platform.core import (
    CurrencyReference,
    InstrumentReference,
    InvalidCurrencyReferenceError,
    InvalidInstrumentReferenceError,
)


def main() -> None:
    instrument = InstrumentReference("figi", "BBG000B9XRY4")
    equivalent_instrument = InstrumentReference("FIGI", "BBG000B9XRY4")
    currency = CurrencyReference("usd")
    equivalent_currency = CurrencyReference("USD")

    assert instrument.identification_scheme == "FIGI"
    assert instrument.identification_value == "BBG000B9XRY4"
    assert currency.currency_code == "USD"
    assert instrument == equivalent_instrument
    assert currency == equivalent_currency
    assert instrument.semantic_identity == equivalent_instrument.semantic_identity
    assert currency.semantic_identity == equivalent_currency.semantic_identity
    assert instrument != InstrumentReference("ISIN", "BBG000B9XRY4")
    assert instrument != currency

    try:
        InstrumentReference(" FIGI", "BBG000B9XRY4")
    except InvalidInstrumentReferenceError:
        pass
    else:
        raise AssertionError("Invalid instrument reference was accepted.")

    try:
        CurrencyReference("U1D")
    except InvalidCurrencyReferenceError:
        pass
    else:
        raise AssertionError("Invalid currency reference was accepted.")

    print("Reference identity demo passed.")


if __name__ == "__main__":
    main()
