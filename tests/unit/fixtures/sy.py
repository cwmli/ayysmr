import pytest
import sqlalchemy.orm.query

import ayysmr_web.sy

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
    monkeypatch.setattr(ayysmr_web.sy, "_update_user_tokens", lambda _: None)