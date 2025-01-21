from app.data_sources import FILE_RATE
from app.error import APIError
import datetime


def parse_file():
    data = []
    with open(FILE_RATE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split("\t")
            _, date_str, rate_str = parts
            try:
                parsed_date = datetime.datetime.strptime(date_str, "%d/%m/%Y").strftime(
                    "%Y/%m/%d"
                )
                rate = int(rate_str)
                currency_value = round((1 / (rate / 10000000)) * 1000, 2)
                obj_value = {"date": parsed_date, "currency_value": currency_value}
                data.append(obj_value)
            except ValueError:
                raise APIError(500, f"Unexpected exception with data graph")
    data_sorted = sorted(data, key=lambda x: x["date"])
    return data_sorted
