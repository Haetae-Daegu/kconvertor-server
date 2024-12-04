import requests, os
from app.api import API_URL
from app.error import APIError
from flask import Blueprint, request

api_bp = Blueprint("api_bp", __name__)


@api_bp.route("/currency/", methods=["POST"])
def json_currency():
    print(request.json)
    from_currency = request.json["from_currency"]
    to_currency = request.json["to_currency"]
    amount = request.json["amount"]

    if not from_currency or not to_currency or amount is None:
        return APIError(400, f"error: Missing required parameters")

    return exchange_rate(from_currency, to_currency, amount)


def exchange_rate(
    from_currency: str = "EUR", to_currency: str = "KRW", amount: float = 1
):
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    url = f"{API_URL}{api_key}/pair/{from_currency}/{to_currency}/{amount}"

    try:
        response = requests.get(url)
        if response.status_code == 403:
            raise APIError(403, "Forbidden: Access to the API is denied")

        data = response.json()
        print(data)

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
