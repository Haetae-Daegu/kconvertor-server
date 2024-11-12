import requests, os
from app.api import FROM_COUNTRY, TO_COUNTRY, API_URL
from flask import Blueprint

api_bp = Blueprint("api_bp", __name__)


@api_bp.route('/currency/')
def json_currency():
    country = FROM_COUNTRY
    return exchange_rate(country)

def exchange_rate(country="EUR"):
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    url = f"{API_URL} + {api_key}/latest/{country}"
    try:
        response = requests.get(url)
        data = response.json()
        conversion_rate = data["conversion_rates"]
        obj_dict = get_countries(data["base_code"], conversion_rate)
        return obj_dict
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")
        return err

def get_countries(base_code, conversion_rate):
    dict = {}
    dict[base_code] = conversion_rate[base_code]
    dict[TO_COUNTRY] = conversion_rate[TO_COUNTRY]
    return dict