import requests, os
from app.error import APIError
from app.data_sources import API_URL, FROM_CURRENCY, TO_CURRENCY

exchange_rate_api_key = os.environ.get("EXCHANGE_RATE_API_KEY")


def exchange_rate(
    from_currency: str = FROM_CURRENCY,
    to_currency: str = TO_CURRENCY,
    amount: float = 1,
):
    url = (
        f"{API_URL}{exchange_rate_api_key}/pair/{from_currency}/{to_currency}/{amount}"
    )

    try:
        response = requests.get(url)
        if response.status_code == 403:
            raise APIError(403, "Forbidden: Access to the API is denied")

        data = response.json()
        return get_conversion_rate(data, amount)

    except requests.exceptions.RequestException as err:
        raise APIError(500, f"Connection Error: {err}")
    except Exception as e:
        raise APIError(500, f"Unexpected Exception: {e} is incorrect or missing")


def get_conversion_rate(data, amount: float):
    return {
        data["base_code"]: amount,
        data["target_code"]: round(data["conversion_result"], 2),
    }
