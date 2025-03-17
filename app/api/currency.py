from app.error import APIError
from app.data_sources.currency import exchange_rate
from flask import Blueprint, request

currency_bp = Blueprint("currency_bp", __name__)


@currency_bp.route("/currency/", methods=["POST"])
def json_currency():
    from_currency = request.json["from_currency"]
    to_currency = request.json["to_currency"]
    amount = request.json["amount"]

    if not from_currency or not to_currency or amount is None:
        return APIError(400, f"error: Missing required parameters")

    return exchange_rate(from_currency, to_currency, amount)
