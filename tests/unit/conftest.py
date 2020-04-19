import pytest
import os

from ayysmr_web.app import make_app

from .fixtures.sy import mock_get_access_token, mock_get_user_profile, mock_get_db

@pytest.fixture
def app():
    app = make_app({
        "APP_SECRET_KEY": b'test',
        "SY_CLIENT_ID": '',
        "SY_CLIENT_SECRET": '',
        "SQLALCHEMY_DATABASE_URI": '"sqlite:///:memory:"',
        "TESTING": True
    })

    yield app

@pytest.fixture
def client(app):
    return app.test_client()