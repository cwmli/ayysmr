# Testing behavior of /sy/callback endpoint
# in cases where there is an invalid/non-existent state,
# no access_token granted, updating or adding user
# tokens for old or new users

class TestSyCallbackEndpoint:

    def test_no_state_sy_callback(self, client):

        client.get('/sy/callback')
        with client.session_transaction() as session:
            msg = dict(session['_flashes']).get('error')
        
        assert 'Invalid state' in msg

    def test_invalid_state_sy_callback(self, client):

        with client.session_transaction() as session:
            session['state'] = 'abc123'

        client.get('/sy/callback?state=abc121')
        with client.session_transaction() as session:
            msg = dict(session['_flashes']).get('error')

        assert 'Invalid state' in msg

    def test_no_token_sy_callback(self, client):

        with client.session_transaction() as session:
            session['state'] = 'abc123'
        
        client.get('/sy/callback?state=abc123')
        with client.session_transaction() as session:
            msg = dict(session['_flashes']).get('error')

        assert 'Failed to authorize' in msg


    def test_tokens_set_sy_callback(self, client, mock_get_access_token, mock_get_user_profile, mock_get_db):

        with client.session_transaction() as session:
            session['state'] = 'abc123'
        
        client.get('/sy/callback?state=abc123')

        with client.session_transaction() as session:
            sessionKeys = session.keys()

        assert 'access_token' in sessionKeys
        assert 'expire_time' in sessionKeys
        assert 'user' in sessionKeys