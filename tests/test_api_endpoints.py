"""API integration tests for core endpoints."""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

import api.main as api_main
from data.database import create_action_task

client = TestClient(api_main.app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_progress_endpoint_shape():
    user_id = f"api-progress-{uuid.uuid4()}"
    response = client.get("/progress", params={"user_id": user_id})
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == user_id
    assert "history" in payload
    assert "insight" in payload
    assert "action_status" in payload


def test_plan_and_action_update_flow():
    user_id = f"api-plan-{uuid.uuid4()}"
    action_id = str(uuid.uuid4())
    create_action_task(
        user_id=user_id,
        action_id=action_id,
        target="Priya",
        action_text="Send a check-in message to Priya",
    )

    plan_response = client.get("/plan", params={"user_id": user_id})
    assert plan_response.status_code == 200
    assert len(plan_response.json()["actions"]) >= 1

    complete_response = client.post(
        "/plan/action",
        json={
            "user_id": user_id,
            "action_id": action_id,
            "status": "completed",
            "blocker_reason": "",
        },
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"


def test_device_token_registration():
    response = client.post(
        "/notifications/device-token",
        json={"user_id": "default", "token": "dummy-token", "platform": "android"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_chat_response_includes_structured_data():
    user_id = f"api-chat-{uuid.uuid4()}"
    response = client.post(
        "/chat",
        json={"user_id": user_id, "message": "I miss Priya and we used to talk often."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "response_text" in payload
    assert "structured_data" in payload


def test_api_auth_middleware_requires_header_when_enabled():
    old_token = api_main.API_AUTH_TOKEN
    try:
        api_main.API_AUTH_TOKEN = "test-secret"
        unauthorized = client.get("/progress", params={"user_id": "auth-check"})
        assert unauthorized.status_code == 401

        authorized = client.get(
            "/progress",
            params={"user_id": "auth-check"},
            headers={"x-api-key": "test-secret"},
        )
        assert authorized.status_code == 200
    finally:
        api_main.API_AUTH_TOKEN = old_token
