import pytest
from fastapi.testclient import TestClient

from luki_modules_engagement.main import app
import luki_modules_engagement.main as engagement_main


@pytest.mark.asyncio
async def test_recommendations_blocked_when_policy_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_enforce_engagement_policy(user_id: str, requested_scopes=None, context=None):  # type: ignore[override]
        return {"allowed": False, "error": "consent_denied"}

    monkeypatch.setattr(engagement_main, "_enforce_engagement_policy", fake_enforce_engagement_policy)

    client = TestClient(app)
    response = client.get("/recommendations/test_user")

    assert response.status_code == 403
    data = response.json()
    assert isinstance(data.get("detail"), dict)
    assert data["detail"].get("error") == "consent_denied"
