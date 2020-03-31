import os
import hashlib

from flask import Flask

from ayysmr_web.store import db, migrate
from ayysmr_web.sy import sy

def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    if config is None:
        app.config.from_pyfile('./configs/default.cfg', silent=True)
    else:
        app.config.from_mapping(config)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.secret_key = app.config['APP_SECRET_KEY']

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(sy)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
