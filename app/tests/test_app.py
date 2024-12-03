import pytest
import requests
from app.tests.conftest import client
from app.api import API_URL

country = "EUR"
from_currency = "EUR"
to_currency = "KRW"
amount = 1
FAKE_API_KEY = "fake_api_key"


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv("EXCHANGE_RATE_API_KEY", "fake_api_key")


def test_create_app(client):
    response = client.get("/")
    assert response.status_code == 200

def test_currency_route_connection_error(client, mock_requests):
    url = f"{API_URL}{FAKE_API_KEY}/pair/{from_currency}/{to_currency}/{amount}"
    mock_requests.get(url, exc=requests.exceptions.ConnectionError)
    response = client.post("/currency/", json={
        "from_currency": from_currency,
        "to_currency": to_currency,
        "amount": amount
    })

    assert response.status_code == 500
    assert "Error" in response.get_data(as_text=True)
