from .app import *
from .store import celery

def create_app(mode):
    app = make_app()
    make_celery(app, celery)

    from .jobs.tracks import retPlayHistory
    retPlayHistory.delay(0, 50)

    if mode == 'app':
        return app
    elif mode == 'celery':
        return celery