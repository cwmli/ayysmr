import os
import hashlib

from flask import Flask

from .store import db, migrate
from .sy import sy

def make_app(config=None):
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

def make_celery(app, celery):
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            # exc (Exception) - The exception raised by the task.
            # args (Tuple) - Original arguments for the task that failed.
            # kwargs (Dict) - Original keyword arguments for the task that failed.
            print('{0!r} failed: {1!r}'.format(task_id, exc))

    celery.Task = ContextTask

    celery.finalize()