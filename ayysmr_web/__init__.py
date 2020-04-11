from .app import *
from .jobs.tasks import celery

def create_app(mode):
    app = make_app()
    make_celery(app, celery)

    if mode == 'app':
        return app
    elif mode == 'celery':
        return celery