import logging
from os.path import join

import redis
from apscheduler import events

from suricate.schedulers import Scheduler
from suricate.configuration import config
from suricate.errors import CannotGetComponentError, ComponentAttributeError

logger = logging.getLogger('suricate')
r = redis.StrictRedis()


class Publisher(object):

    s = Scheduler()

    def __init__(self, *args):
        """Initialize a Publisher instance.

        It takes zero, one or three arguments.

        One argument: a (JSON) dictionary
        -------------------------------
        In this case the argument must be a dictionary. Each key is a component
        name, and each value is a list of attributes to publish. This is an
        example::

            config = {
                "TestNamespace/Positioner00":
                    [
                        {"attribute": "position", "timer": 0.1},
                        {"attribute": "current", "timer": 0.1},
                    ],
                "TestNamespace/Positioner01":
                    [
                        {"attribute": "current", "timer": 0.1},
                    ]
            }
            publisher = Publisher(config)


        Three arguments: component name, attribute, timer
        -------------------------------------------------
        For instance::

            publisher = Publisher('TestNamespace/Positioner', 'position', 0.1)
        """
        if len(args) == 0:
            pass
        elif len(args) == 1:  # The argument must be a (JSON) dictionary
            self.add_jobs(*args)
        else:  # Expected arguments: component name, attribute name, timer
            comp, attr, timer = args
            self.add_jobs({comp: [{'attribute': attr, 'timer': timer}]})

        Publisher.add_errors_listener()
        self.s.add_job(
            func=self.rescheduler,
            args=(),
            id='rescheduler',
            trigger='interval',
            seconds=config['SCHEDULER']['RESCHEDULE_INTERVAL']
        )

    def add_jobs(self, config):
        """
        {
            "TestNamespace/Positioner":
            [
                {
                    "attribute": "position",
                    "description": "actual position",
                    "timer": 0.1
                }
            ]
        }
        """
        args = []  # list of tuples [(component, attribute_name, timer), (...)]
        from suricate.services import Component
        for component_name, attributes in config.items():
            try:
                c = Component(component_name)
            except CannotGetComponentError:
                logger.error('cannot get component %s' % component_name)
                continue
            prefix = c.device_attribute_prefix
            for a in attributes:
                if hasattr(c, prefix + a['attribute']):
                    args.append((c, a['attribute'], a['timer']))
                    job_id = '%s/%s' % (component_name, a['attribute'])
                    r.delete('error_job:%s' % job_id)
                    r.delete('healthy_job:%s' % job_id)
                else:
                    logger.error('%s has not attribute %s' % (c.name, a['attribute']))
                        

        for arg in args:
            self.s.add_attribute_job(*arg)


    def rescheduler(self):
        for job in self.get_jobs():
            error_job_key = 'error_job:%s' % job.id
            healthy_job_key = 'healthy_job:%s' % job.id
            interval_time = r.get(error_job_key)
            if interval_time and r.get(healthy_job_key):
                r.delete(error_job_key)
                self.s.reschedule_job(
                    job.id,
                    trigger='interval',
                    seconds=float(interval_time)
                )
        
    def get_jobs(self):
        return self.s.get_jobs()

    @classmethod
    def add_errors_listener(cls):
        cls.s.add_listener(cls.errors_listener, events.EVENT_JOB_ERROR)

    @staticmethod
    def errors_listener(event):
        job_id = event.job_id
        healthy_job_key = 'healthy_job:%s' % job_id
        r.delete(healthy_job_key)
        if isinstance(
                event.exception,
                (CannotGetComponentError, ComponentAttributeError)):
            job = Publisher.s.get_job(job_id)
            error_job_key = 'error_job:%s' % job_id
            if not r.get(error_job_key):
                # Save job.seconds, because we will temporarily change it
                sec, mic = job.trigger.interval.seconds, job.trigger.interval.microseconds
                interval = sec + mic / (1.0 * 10 ** 6)
                r.set(error_job_key, interval)
                # Slowdown the job, until the component comes available
                Publisher.s.reschedule_job(
                    job_id,
                    trigger='interval',
                    seconds=config['SCHEDULER']['RESCHEDULE_ERROR_INTERVAL']
                )

            channel, old_component_ref, attribute = job.args
            from suricate.services import Component
            # If the component is available, we pass its reference to the job
            # and we restore the original job heartbeat
            try:
                component_ref = Component(old_component_ref.name)
                args = channel, component_ref, attribute
                Publisher.s.modify_job(job_id, args=args)
            except CannotGetComponentError:
                pass  # Do nothing


        else:
            # TODO: manage the unexpected exception
            pass

    @classmethod
    def start(cls):
        cls.s.start()

    @classmethod
    def shutdown(cls):
        for job in cls.s.get_jobs():
            job.remove()
        cls.s.shutdown(wait=False)
        cls.s = Scheduler()
