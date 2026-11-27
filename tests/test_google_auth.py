import pytest
from flask_jwt_extended import create_access_token, create_refresh_token
from google.auth import exceptions as google_exceptions

from app.models.accommodation import Accommodation
from app.models.user import User
from app.services.auth_service import hash_password

CLIENT_ID = "test-client-id.apps.googleusercontent.com"
VERIFY = "app.services.auth_service.id_token.verify_oauth2_token"


def google_claims(**overrides):
    claims = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "google-sub-123",
        "email": "jane@gmail.com",
        "email_verified": True,
        "name": "Jane Doe",
        "picture": "https://lh3.googleusercontent.com/a/jane.png",
    }
    claims.update(overrides)
    return claims


@pytest.fixture(autouse=True)
def alerts(mocker):
    """Never call Discord; expose the auth alert mock to the tests."""
    mocker.patch("app.api.user.send_alert")
    return mocker.patch("app.api.auth.send_alert")


@pytest.fixture
def hashed_password(db, test_user):
    """Give test_user a real bcrypt hash ("password123") so it can log in."""
    test_user.password = hash_password("password123")
    db.session.commit()


@pytest.fixture
def verify(mocker):
    return mocker.patch(VERIFY, return_value=google_claims())


def google_login(client, credential="a-google-id-token"):
    return client.post("/auth/google", json={"credential": credential})


def registration_alerts(alerts):
    return [c for c in alerts.call_args_list if c.args[0] == "Registration"]


# --- POST /auth/google ---------------------------------------------------


def test_new_google_user_is_created(client, db, verify, alerts):
    response = google_login(client)

    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {"id", "email", "username", "access_token", "refresh_token"}
    assert body["email"] == "jane@gmail.com"
    assert body["username"] == "Jane Doe"

    user = db.session.get(User, body["id"])
    assert user.google_sub == "google-sub-123"
    assert user.auth_provider == "google"
    assert user.password is None
    assert user.avatar_url == "https://lh3.googleusercontent.com/a/jane.png"

    assert len(registration_alerts(alerts)) == 1
    assert "jane@gmail.com" in registration_alerts(alerts)[0].args[1]


def test_token_is_checked_against_our_client_id(client, verify):
    google_login(client, credential="the-token")

    credential, _request, audience = verify.call_args.args
    assert credential == "the-token"
    assert audience == CLIENT_ID


def test_returned_access_token_works_on_me(client, verify):
    token = google_login(client).get_json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    me = response.get_json()
    assert me["email"] == "jane@gmail.com"
    assert me["auth_provider"] == "google"
    assert me["has_password"] is False


def test_existing_google_sub_logs_in(client, db, verify, alerts):
    first = google_login(client).get_json()
    alerts.reset_mock()

    # Same Google account, even if its email changed meanwhile.
    verify.return_value = google_claims(email="jane.new@gmail.com")
    second = google_login(client)

    assert second.status_code == 200
    assert second.get_json()["id"] == first["id"]
    assert User.query.count() == 1
    assert registration_alerts(alerts) == []


def test_verified_email_links_existing_account(
    client, db, test_user, hashed_password, test_accommodation, verify, alerts
):
    verify.return_value = google_claims(email=test_user.email.upper())

    response = google_login(client)

    assert response.status_code == 200
    assert response.get_json()["id"] == test_user.id
    db.session.refresh(test_user)
    assert test_user.google_sub == "google-sub-123"
    assert test_user.auth_provider == "local"
    assert User.query.count() == 1
    assert Accommodation.query.filter_by(host_id=test_user.id).count() == 1
    assert registration_alerts(alerts) == []

    # The password still works after linking.
    login = client.post(
        "/auth/login", json={"email": test_user.email, "password": "password123"}
    )
    assert login.status_code == 200


def test_unverified_email_does_not_link(client, db, test_user, verify):
    verify.return_value = google_claims(email=test_user.email, email_verified=False)

    response = google_login(client)

    assert response.status_code == 409
    db.session.refresh(test_user)
    assert test_user.google_sub is None
    assert User.query.count() == 1


def test_email_linked_to_another_google_account_is_refused(
    client, db, test_user, verify
):
    test_user.google_sub = "another-google-sub"
    db.session.commit()
    verify.return_value = google_claims(email=test_user.email)

    response = google_login(client)

    assert response.status_code == 409
    db.session.refresh(test_user)
    assert test_user.google_sub == "another-google-sub"


def test_unverified_email_without_account_creates_user(client, db, verify):
    verify.return_value = google_claims(email_verified=False)

    response = google_login(client)

    assert response.status_code == 200
    assert User.query.filter_by(google_sub="google-sub-123").count() == 1


@pytest.mark.parametrize(
    "error",
    [
        ValueError("Token expired"),
        ValueError("Token has wrong audience"),
        google_exceptions.GoogleAuthError("Wrong issuer"),
    ],
)
def test_invalid_token_returns_401(client, db, mocker, error):
    mocker.patch(VERIFY, side_effect=error)

    response = google_login(client)

    assert response.status_code == 401
    assert User.query.count() == 0


def test_google_unreachable_returns_503(client, mocker):
    mocker.patch(VERIFY, side_effect=google_exceptions.TransportError("timeout"))

    assert google_login(client).status_code == 503


@pytest.mark.parametrize("payload", [{}, {"credential": ""}, {"credential": 42}])
def test_missing_credential_returns_400(client, verify, payload):
    response = client.post("/auth/google", json=payload)

    assert response.status_code == 400
    verify.assert_not_called()


def test_refused_when_client_id_is_not_configured(app, client, verify):
    app.config["GOOGLE_CLIENT_ID"] = None

    response = google_login(client)

    assert response.status_code == 503
    verify.assert_not_called()


def test_username_collision_gets_numeric_suffix(client, db, verify):
    for username, email in [("Jane Doe", "a@x.com"), ("Jane Doe2", "b@x.com")]:
        db.session.add(User(username=username, email=email, password="x"))
    db.session.commit()

    response = google_login(client)

    assert response.status_code == 200
    assert response.get_json()["username"] == "Jane Doe3"


def test_username_falls_back_to_email_local_part(client, verify):
    verify.return_value = google_claims(name=None, email="jdoe42@gmail.com")

    assert google_login(client).get_json()["username"] == "jdoe42"


def test_two_google_users_with_same_name(client, verify):
    first = google_login(client).get_json()
    verify.return_value = google_claims(sub="other-sub", email="jane2@gmail.com")
    second = google_login(client).get_json()

    assert first["username"] == "Jane Doe"
    assert second["username"] == "Jane Doe2"


# --- POST /auth/login with a Google-only account ---------------------------


def test_password_login_on_google_only_account(client, verify):
    google_login(client)

    response = client.post(
        "/auth/login", json={"email": "jane@gmail.com", "password": "anything"}
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "This account uses Google sign-in"


# --- POST /users/change-password -------------------------------------------


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_google_user_can_set_a_first_password(client, db, verify):
    token = google_login(client).get_json()["access_token"]

    response = client.post(
        "/users/change-password",
        json={"new_password": "brand-new-pass"},
        headers=auth(token),
    )

    assert response.status_code == 200
    user = User.query.filter_by(email="jane@gmail.com").first()
    assert user.password.startswith("$2b$")
    login = client.post(
        "/auth/login", json={"email": "jane@gmail.com", "password": "brand-new-pass"}
    )
    assert login.status_code == 200


def test_change_password_requires_current_password(client, test_user, user_token):
    for payload in [
        {"new_password": "brand-new-pass"},
        {"current_password": "wrong", "new_password": "brand-new-pass"},
    ]:
        response = client.post(
            "/users/change-password", json=payload, headers=auth(user_token)
        )
        assert response.status_code == 401


def test_change_password_with_current_password(
    client, db, test_user, hashed_password, user_token
):
    response = client.post(
        "/users/change-password",
        json={"current_password": "password123", "new_password": "brand-new-pass"},
        headers=auth(user_token),
    )

    assert response.status_code == 200
    db.session.refresh(test_user)
    assert test_user.password.startswith("$2b$")
    old = client.post(
        "/auth/login", json={"email": test_user.email, "password": "password123"}
    )
    new = client.post(
        "/auth/login", json={"email": test_user.email, "password": "brand-new-pass"}
    )
    assert old.status_code == 401
    assert new.status_code == 200


def test_change_password_rejects_short_password(
    client, test_user, hashed_password, user_token
):
    response = client.post(
        "/users/change-password",
        json={"current_password": "password123", "new_password": "abc"},
        headers=auth(user_token),
    )

    assert response.status_code == 400


def test_change_password_requires_auth(client):
    response = client.post("/users/change-password", json={"new_password": "abcdef"})

    assert response.status_code == 401


# --- POST /auth/refresh ----------------------------------------------------


def test_refresh_with_token_in_body(client, test_user):
    refresh = create_refresh_token(identity=str(test_user.id))

    response = client.post("/auth/refresh", json={"refresh_token": refresh})

    assert response.status_code == 200
    body = response.get_json()
    assert body["access_token"] and body["refresh_token"]
    me = client.get("/auth/me", headers=auth(body["access_token"]))
    assert me.status_code == 200


def test_refresh_with_token_in_header(client, test_user):
    refresh = create_refresh_token(identity=str(test_user.id))

    response = client.post("/auth/refresh", headers=auth(refresh))

    assert response.status_code == 200


def test_refresh_rejects_access_token(client, test_user):
    access = create_access_token(identity=str(test_user.id))

    response = client.post("/auth/refresh", json={"refresh_token": access})

    assert response.status_code == 401


def test_refresh_without_token(client):
    assert client.post("/auth/refresh", json={}).status_code == 401


def test_public_profile_hides_auth_details(client, verify):
    user_id = google_login(client).get_json()["id"]

    profile = client.get(f"/users/{user_id}").get_json()

    assert profile["avatar_url"] == "https://lh3.googleusercontent.com/a/jane.png"
    assert "has_password" not in profile
    assert "auth_provider" not in profile
