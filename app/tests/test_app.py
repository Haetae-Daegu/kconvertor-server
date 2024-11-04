from app.tests.conftest import client

def test_create_app(client):
    response = client.get('/')
    assert response.status_code == 200