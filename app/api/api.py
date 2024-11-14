import requests, os
from app.api import FROM_CURRENCY, TO_CURRENCY, API_URL
from app.error import APIError
from flask import Blueprint

api_bp = Blueprint("api_bp", __name__)


@api_bp.route("/currency/")
def json_currency():
    country = FROM_CURRENCY
    return exchange_rate(country)


def exchange_rate(country="EUR"):
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    url = f"{API_URL}{api_key}/latest/{country}"

    try:
        response = requests.get(url)
        if response.status_code == 403:
            raise APIError(403, "Forbidden: Access to the API is denied")

        data = response.json()
        conversion_rate = data["conversion_rates"]

        return get_conversion_rate(conversion_rate)

    except requests.exceptions.RequestException as err:
        raise APIError(500, f"Connection Error: {err}")


def get_conversion_rate(conversion_rate):
    return {
        FROM_CURRENCY: conversion_rate[FROM_CURRENCY],
        TO_CURRENCY: conversion_rate[TO_CURRENCY],
    }
