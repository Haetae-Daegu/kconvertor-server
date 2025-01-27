from app.data_sources import FILE_RATE
from app.error import APIError
import datetime


def parse_file():
    data = []
    with open(FILE_RATE, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split("\t")
            _, date_str, currency_value = parts
            try:
                
                obj_value = {"date": date_str, "currency_value": float(currency_value)}
                data.append(obj_value)
            except ValueError:
                raise APIError(500, f"Unexpected exception with data graph")
    return data
