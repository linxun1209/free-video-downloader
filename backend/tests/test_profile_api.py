import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import database
import main
import api_auth


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test_profile_api.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()
    with TestClient(main.app) as test_client:
        yield test_client


def _register_and_get_token(client: TestClient, email: str = "alice@example.com") -> tuple[str, dict]:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    body = response.json()
    return body["data"]["token"], body["data"]["user"]


def test_profile_requires_login(client: TestClient):
    response = client.get("/api/auth/profile")
    assert response.status_code == 401
    assert response.json()["detail"] == "请先登录"


def test_profile_get_and_update_flow(client: TestClient):
    token, register_user = _register_and_get_token(client)
    assert register_user["nickname"] == ""
    assert register_user["phone"] == ""
    assert register_user["bio"] == ""

    headers = {"Authorization": f"Bearer {token}"}
    profile_response = client.get("/api/auth/profile", headers=headers)
    assert profile_response.status_code == 200
    profile_data = profile_response.json()["data"]
    assert profile_data["nickname"] == ""
    assert profile_data["phone"] == ""
    assert profile_data["bio"] == ""

    update_response = client.put(
        "/api/auth/profile",
        headers=headers,
        json={
            "nickname": "Alice",
            "phone": "+1 555 0101",
            "bio": "Loves long-form summaries.",
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["nickname"] == "Alice"
    assert updated["phone"] == "+1 555 0101"
    assert updated["bio"] == "Loves long-form summaries."

    login_response = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    login_user = login_response.json()["data"]["user"]
    assert login_user["nickname"] == "Alice"
    assert login_user["phone"] == "+1 555 0101"
    assert login_user["bio"] == "Loves long-form summaries."


def test_profile_update_rejects_too_long_nickname(client: TestClient):
    token, _ = _register_and_get_token(client, email="bob@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/api/auth/profile",
        headers=headers,
        json={"nickname": "a" * 31, "phone": "", "bio": ""},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "昵称长度不能超过 30 个字符"


def test_profile_update_accepts_values_valid_after_trimming(client: TestClient):
    token, _ = _register_and_get_token(client, email="carol@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/api/auth/profile",
        headers=headers,
        json={
            "nickname": f"{'n' * 30}   ",
            "phone": "  +1 555 0102  ",
            "bio": "  hello world  ",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nickname"] == "n" * 30
    assert data["phone"] == "+1 555 0102"
    assert data["bio"] == "hello world"


def test_profile_partial_update_ignores_untouched_padded_field_length(client: TestClient):
    token, _ = _register_and_get_token(client, email="dave@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    me_response = client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_id = me_response.json()["data"]["id"]

    with database.get_db() as conn:
        conn.execute(
            "UPDATE users SET nickname = ? WHERE id = ?",
            (f"{'k' * 30}   ", user_id),
        )

    response = client.put(
        "/api/auth/profile",
        headers=headers,
        json={"phone": "  123456  "},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nickname"] == "k" * 30
    assert data["phone"] == "123456"


def test_profile_update_returns_401_when_persisted_user_missing_after_auth(client: TestClient, monkeypatch):
    token, _ = _register_and_get_token(client, email="erin@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    def _missing_user_after_update(user_id: int, nickname: str | None, phone: str | None, bio: str | None):
        return None

    monkeypatch.setattr(api_auth, "update_user_profile", _missing_user_after_update)

    response = client.put(
        "/api/auth/profile",
        headers=headers,
        json={"nickname": "Erin"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "用户不存在"
