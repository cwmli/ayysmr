from celery import Celery
from celery.schedules import crontab

celery = Celery(__name__, autofinalize=False)

@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    from .tracks import retPlayHistory
    # Update play histories on midnight daily
    sender.add_periodic_task(
        crontab(minute=0, hour=0),
        retPlayHistory.s(0, 25, 1)
    )