import requests, os
from flask import Blueprint

api_bp = Blueprint("api_bp", __name__)




@api_bp.route('/currency/')
def json_currency():
    country = os.environ.get("COUNTRY")
    return exchange_rate(country)

def exchange_rate(country="USD"):
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{country}"
    response = requests.get(url)
    data = response.json()
    #TODO: Create function to handle error for requests

    conversion_rate = data["conversion_rates"]
    obj_dict = get_countries(data["base_code"], conversion_rate)
    return obj_dict


def get_countries(base_code, conversion_rate):
    dict = {}
    dict[base_code] = conversion_rate[base_code]
    dict["KRW"] = conversion_rate["KRW"]
    return dict