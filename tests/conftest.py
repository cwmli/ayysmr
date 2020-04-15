import pytest
import os

from ayysmr_web.app import make_app
from ayysmr_web.store import db

with open(os.path.join(os.path.dirname(__file__), 'testdata.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')

@pytest.fixture
def app():
    app = make_app({
        "APP_SECRET_KEY": b'test',
        "SY_CLIENT_ID": '',
        "SY_CLIENT_SECRET": '',
        "SQLALCHEMY_DATABASE_URI": 'postgresql://calvinli@localhost/ayysmr_test',
        "CELERY_BROKER_URL": 'amqp://localhost',
        "CELERY_RESULT_BACKEND": 'db+postgresql://calvinli@localhost/ayysmr_test',
        "TESTING": True
    })

    with app.app_context():
        # reset the database
        db.drop_all()
        db.create_all()
        with db.engine.connect() as connection:
            connection.execute(_data_sql)

    yield app

@pytest.fixture
def client(app):
    return app.test_client()