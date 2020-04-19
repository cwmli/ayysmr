import pytest

import ayysmr_web

@pytest.fixture
def mock_get_access_token(monkeypatch):
    monkeypatch.setattr(ayysmr_web.utils.spotify, "get_access_token", lambda _: {
        "access_token": "newtoken",
        "expires_in": 0,
        "refresh_token": "newtoken"
    })