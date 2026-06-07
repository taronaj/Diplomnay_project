import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main_admin import app

client = TestClient(app)


def _login(username: str = "admin", password: str = "admin123") -> str:
    response = client.post("/frontend-api/sign-in", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_returns_jwt():
    token = _login()
    assert token


def test_dashboard_requires_token():
    response = client.get("/frontend-api/dashboard-data")
    assert response.status_code == 401


def test_create_course_with_admin_token():
    token = _login()
    response = client.post(
        "/frontend-api/courses",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test Course", "price": 100, "description": "Created by test"},
    )
    assert response.status_code in (200, 201)


def test_attendance_with_admin_token():
    token = _login()
    response = client.post(
        "/frontend-api/attendance",
        headers={"Authorization": f"Bearer {token}"},
        json={"attended": True},
    )
    assert response.status_code in (200, 201)
