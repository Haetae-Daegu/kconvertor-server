import pytest
import requests_mock

from app.app import create_app


@pytest.fixture
def client():
    app = create_app()
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_requests():
    with requests_mock.Mocker() as mock:
        yield mock
