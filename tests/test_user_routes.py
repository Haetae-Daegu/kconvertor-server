import json


def test_list_users(client):
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(json.loads(response.data), list)


def test_get_user(client, test_user):
    response = client.get(f"/users/{test_user.id}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email


def test_get_nonexistent_user(client):
    response = client.get("/users/9999")
    assert response.status_code == 404


def test_create_user(client):
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpassword123",
    }
    response = client.post(
        "/users/", data=json.dumps(user_data), content_type="application/json"
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]


def test_create_user_invalid_data(client):
    user_data = {"username": "invalid", "password": "short"}
    response = client.post(
        "/users/", data=json.dumps(user_data), content_type="application/json"
    )
    assert response.status_code == 400


def test_update_user(client, test_user, user_token):
    update_data = {"username": "updateduser", "email": "updated@example.com"}
    response = client.put(
        f"/users/{test_user.id}",
        data=json.dumps(update_data),
        content_type="application/json",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["username"] == update_data["username"]
    assert data["email"] == update_data["email"]


def test_update_nonexistent_user(client, user_token):
    update_data = {"username": "updateduser", "email": "updated@example.com"}
    response = client.put(
        "/users/9999",
        data=json.dumps(update_data),
        content_type="application/json",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 404


def test_delete_user(client, test_user, user_token):
    response = client.delete(
        f"/users/{test_user.id}", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200

    response = client.get(f"/users/{test_user.id}")
    assert response.status_code == 404


def test_delete_nonexistent_user(client, user_token):
    response = client.delete(
        "/users/9999", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 404
