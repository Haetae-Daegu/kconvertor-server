from typing import TypedDict


class CountryCode(str):

    def __new__(cls, value: str) -> "CountryCode":

        value = super().__new__(cls, value)
        if len(value) != 3:
            raise ValueError("Country code must be 3 characters")

        return value


class CurrencyRate(float):

    def __new__(cls, value: float) -> "CurrencyRate":

        value = super().__new__(cls, value)
        if value < 0:
            raise ValueError("Conversion rate must be positive")

        return value


class ExchangeRate(TypedDict):
    from_currency: CountryCode
    to_currency: CountryCode
    conversion_rate: CurrencyRate
