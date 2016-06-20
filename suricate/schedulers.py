import logging

from apscheduler.schedulers.background import BackgroundScheduler
from suricate import jobs


__all__ = ['Scheduler']

logging.basicConfig()


class ACSScheduler(BackgroundScheduler):
    """TODO:
    - add_method_job: like add_property_job(), but for methods
    - It should delegate... or proxy
    """

    def add_attribute_job(self, component_ref, attr, seconds, channel=''):
        """TODO: docstring. The component could be a name or an instance"""
        # Job identifier: namespace/component/attribute
        job_id = '/'.join([component_ref.name, attr])
        channel = channel if channel else job_id
        return super(ACSScheduler, self).add_job(
            func=publisher,
            args=(channel, component_ref, attr),
            id=job_id,
            trigger='interval',
            seconds=seconds)


# TODO: check the configuration and bind the right scheduler
Scheduler = ACSScheduler
publisher = jobs.acs_property_publisher
