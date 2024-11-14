from typing import Dict

import requests

from app.api.types import CountryCode


class ExchangeRateRepository:

    class ForbiddenAccessError(Exception):
        pass

    class UnexpectedResponseError(Exception):
        pass

    def __init__(self, api_url: str, api_key: str):
        self.api_key = api_key
        self.url = f"{api_url}{api_key}/latest/"

    def get_exchange_rate_for_country(self, to_currency: CountryCode, base_currency: CountryCode = "EUR") -> Dict[CountryCode, float]:
        try:
            response = requests.get(f"{self.url}{base_currency}")

            if response.status_code == 403:
                raise self.ForbiddenAccessError("Access to the API is denied")

            data = response.json()
            conversion_rate = data["conversion_rates"]

            return {
                base_currency: conversion_rate[base_currency],
                to_currency: conversion_rate[to_currency],
            }

        except requests.exceptions.RequestException as err:
            raise self.UnexpectedResponseError(f"Unexpected response from API: {err}")

