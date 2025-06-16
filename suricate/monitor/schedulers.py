import redis

from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from suricate.monitor import jobs


__all__ = ['Scheduler']


class ACSScheduler(BackgroundScheduler):

    def __init__(self, *args):
        super().__init__(*args)
        executors = {
            'default': ThreadPoolExecutor(50),
            'processpool': ProcessPoolExecutor(50)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }

        self.configure(
            executors=executors,
            job_defaults=job_defaults,
            timezone=utc
        )

    def add_attribute_job(
            self,
            component_ref,
            attr,
            timer,
            units='',
            description='',
            channel=''):
        # Job identifier: namespace/component/attribute
        job_id = '/'.join([component_ref.name, attr])
        channel = channel if channel else job_id
        r = redis.StrictRedis(decode_responses=True)
        error_job_key = f'error_job:{channel}'
        r.delete(error_job_key)
        return super().add_job(
            func=publisher,
            args=(channel, component_ref, attr, timer, units, description),
            id=job_id,
            trigger='interval',
            seconds=timer
        )


# TODO: check the configuration and bind the right scheduler
Scheduler = ACSScheduler
publisher = jobs.acs_publisher
