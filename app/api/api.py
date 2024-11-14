import os

from flask import Blueprint, jsonify

from app.api import API_URL, FROM_CURRENCY
from app.api.data_sources.exchange_rate_repository import ExchangeRateRepository
from app.api.types import CountryCode, ExchangeRate

api_bp = Blueprint("api_bp", __name__)


@api_bp.route("/currency/")
def json_currency():

    try:
        country = CountryCode(FROM_CURRENCY)

        api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
        url = f"{API_URL}{api_key}/latest/{country}"

        exchange_rate_repository = ExchangeRateRepository(url, api_key)

        exchange_rate = get_exchange_rate(exchange_rate_repository, country)

    except ValueError as err:
        return jsonify({"code": 400, "message": f"Invalid country code : {err}"})
    except ExchangeRateRepository.ForbiddenAccessError as err:
        return jsonify({"code": 403, "message": f"Forbidden: {err}"})
    except (
        ExchangeRateRepository.CurrencyNotFoundError,
        ExchangeRateRepository.TargetCurrencyNotFoundError,
    ) as err:
        return jsonify({"code": 404, "message": f"Currency not found: {err}"})
    except (
        ExchangeRateRepository.UnexpectedResponseError,
        ExchangeRateRepository.RequestHandlerError,
    ) as err:
        return jsonify({"code": 500, "message": f"Internal Server Error: {err}"})

    return jsonify(exchange_rate)


def get_exchange_rate(
    exchange_rate_repository: ExchangeRateRepository,
    to_currency: CountryCode,
    from_currency: CountryCode = "EUR",
) -> ExchangeRate:
    conversion_rates = exchange_rate_repository.get_exchange_rate_for_country(
        to_currency=to_currency, base_currency=from_currency
    )

    return ExchangeRate(
        from_currency=from_currency,
        to_currency=to_currency,
        conversion_rate=conversion_rates[to_currency],
    )
