import pytest
import requests
from app.tests.conftest import client
from app.api import API_URL

country = "EUR"
FAKE_API_KEY = "fake_api_key"

@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv("EXCHANGE_RATE_API_KEY", "fake_api_key")

def test_create_app(client):
    response = client.get('/')
    assert response.status_code == 200

def test_currency_route_403(client, mock_requests):
    url = f"{API_URL}{FAKE_API_KEY}/latest/{country}"
    mock_requests.get(url, status_code=403)
    response = client.get("/currency/")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Error 403: Forbidden. Access to the API is denied"

def test_currency_route_connection_error(client, mock_requests):
    url = f"{API_URL}{FAKE_API_KEY}/latest/{country}"
    mock_requests.get(url, exc=requests.exceptions.ConnectionError)
    response = client.get("/currency/")

    assert response.status_code == 200
    assert "Error" in response.get_data(as_text=True)