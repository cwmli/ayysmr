import pytest

import ayysmr_web.utils
import ayysmr_web.jobs.tracks
from ayysmr_web.models.user import User

from .fixtures.sy import mock_get_access_token

class TestSyEndpointIntegration:

    def test_new_user_callback(self, client, prep_db, mock_get_access_token, celery, monkeypatch):

        monkeypatch.setattr(ayysmr_web.utils.spotify, 'get_user_profile', lambda _: { "id": "testid" })

        with client.session_transaction() as session:
            session['state'] = '123'

        client.get('/sy/callback?state=123')

        # Assert user added to db
        assert User.query.filter(User.id == "testid")
        # Assert job enqueued
        # TODO: Track this somewhere maybe?


    def test_returning_user_callback(self, client, prep_db, mock_get_access_token, monkeypatch):

        monkeypatch.setattr(ayysmr_web.utils.spotify, 'get_user_profile', lambda _: { "id": "existingid" })

        with client.session_transaction() as session:
            session['state'] = '123'

        client.get('/sy/callback?state=123')

        user = User.query.filter(User.id == "existingid").first()

        # Assert updated db entry
        assert user.access_token == "newtoken"
        assert user.refresh_token == "newtoken"
        assert user.expire_time == 0

