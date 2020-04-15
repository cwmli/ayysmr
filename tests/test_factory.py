from ayysmr_web.app import make_app

# Testing app factory configuration parameters
# and ensuring blueprint endpoints are valid
# and returning correct values

def test_app_config():
    assert not make_app().testing
    assert make_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}).testing

def test_hello(client):
    res = client.get('/hello')
    assert res.status_code == 200

def test_sy_enable(client):
    res = client.get('/sy/enable')
    assert res.status_code == 302

def test_sy_callback(client, mocker):
    res = client.get('/sy/callback')
    assert res.status_code == 302