import requests, os

def exchange_rate(country):
    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{country}"
    response = requests.get(url)
    data = response.json()

    conversion_rate = data["conversion_rates"]
    obj_dict = get_countries(data["base_code"], conversion_rate)
    return obj_dict


def get_countries(base_code, conversion_rate):
    dict = {}
    dict[base_code] = conversion_rate[base_code]
    dict["KRW"] = conversion_rate["KRW"]
    return dict