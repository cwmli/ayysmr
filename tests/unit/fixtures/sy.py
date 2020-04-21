import pytest

import ayysmr_web

@pytest.fixture
def mock_get_access_token(monkeypatch):
    monkeypatch.setattr(ayysmr_web.utils.spotify, "get_access_token", lambda _: {
        "access_token": "token",
        "expires_in": 0,
        "refresh_token": "token"
    })

@pytest.fixture
def mock_get_user_profile(monkeypatch):
    monkeypatch.setattr(ayysmr_web.utils.spotify, "get_user_profile", lambda _: { "id": "testid" })

@pytest.fixture
def mock_get_db(monkeypatch):
    monkeypatch.setattr(ayysmr_web.sy, "_update_user_tokens", lambda _a1, _a2, _a3, _a4: None)