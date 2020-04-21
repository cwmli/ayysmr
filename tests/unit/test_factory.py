from ayysmr_web.app import make_app

# Testing app factory configuration parameters
# and ensuring blueprint endpoints are valid
# and returning correct values

class TestAppFactory:
    
    def test_app_config(self):
        assert not make_app().testing
        assert make_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}).testing

    def test_hello(self, client):
        res = client.get('/hello')
        assert res.status_code == 200

    def test_sy_enable(self, client):
        res = client.get('/sy/enable')
        assert res.status_code == 302

    def test_sy_callback(self, client, mocker):
        res = client.get('/sy/callback')
        assert res.status_code == 302