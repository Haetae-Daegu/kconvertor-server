from typing import TypedDict


class CountryCode(str):

    def __new__(cls, value: str) -> "CountryCode":
        if len(value) != 3:
            raise ValueError("Country code must be 3 characters")

        return super().__new__(cls, value)

class ExchangeRate(TypedDict):
    from_currency: CountryCode
    to_currency: CountryCode
    conversion_rate: float
