import pytest
import requests

from app.api import API_URL
from app.tests.conftest import client

country = "EUR"
FAKE_API_KEY = "fake_api_key"


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv("EXCHANGE_RATE_API_KEY", "fake_api_key")


def test_create_app(client):
    response = client.get("/")
    assert response.status_code == 200


def test_currency_route_403(client, mock_requests):
    url = f"{API_URL}{FAKE_API_KEY}/latest/{country}"
    mock_requests.get(url, status_code=403)
    response = client.get("/currency/")

    assert response.status_code == 403
    expected_response = {
        "code": 403,
        "message": "Forbidden: Access to the API is denied",
    }
    assert response.get_json() == expected_response


def test_currency_route_connection_error(client, mock_requests):
    url = f"{API_URL}{FAKE_API_KEY}/latest/{country}"
    mock_requests.get(url, exc=requests.exceptions.ConnectionError)
    response = client.get("/currency/")

    assert response.status_code == 500
    assert "Error" in response.get_data(as_text=True)
