from typing import Dict

import requests

from app.api.types import CountryCode, CurrencyRate


class ExchangeRateRepository:

    class ForbiddenAccessError(Exception):
        pass

    class UnexpectedResponseError(Exception):
        pass

    class RequestHandlerError(Exception):
        pass

    class CurrencyNotFoundError(Exception):
        pass

    class TargetCurrencyNotFoundError(Exception):
        pass

    def __init__(self, api_url: str, api_key: str, request_handler=requests):
        self.base_url = f"{api_url}{api_key}/latest/"
        self.request_handler = request_handler

    def get_exchange_rate_for_country(
        self, to_currency: CountryCode, base_currency: CountryCode = "EUR"
    ) -> Dict[CountryCode, CurrencyRate]:
        try:
            response = self.request_handler.get(f"{self.base_url}{base_currency}")

            if response.status_code == 403:
                raise self.ForbiddenAccessError("Access to the API is denied")
            if response.status_code >= 500:
                raise self.UnexpectedResponseError("Unexpected response from API")
            if response.status_code == 404:
                raise self.CurrencyNotFoundError(
                    f"Currency code {to_currency} not found"
                )

            data = response.json()

            conversion_rate = data.get("conversion_rates")

            if not conversion_rate:
                raise self.UnexpectedResponseError(
                    "Conversion rates not found for the given currency"
                )

            try:
                return {
                    base_currency: CurrencyRate(conversion_rate[base_currency]),
                    to_currency: CurrencyRate(conversion_rate[to_currency]),
                }
            except KeyError:
                raise self.TargetCurrencyNotFoundError(
                    f"Currency code {to_currency} not found"
                )
            except ValueError:
                raise self.UnexpectedResponseError(
                    f"Currency rate received from remote repository is not a valid rate"
                )

        except requests.exceptions.RequestException as err:
            raise self.RequestHandlerError(err)
