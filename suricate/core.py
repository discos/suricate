import logging
import datetime
from os.path import join

import redis
import json
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

        The argument is a dictionary. Each key is a component name,
        and each value is a list of attributes to publish. I.e::

            args = {
                "TestNamespace/Positioner00": {
                    "properties": [
                        {"name": "position", "timer": 0.1},
                        {"name": "current", "timer": 0.1},
                    ],
                    "methods": [
                        {"name": "getPosition", "timer": 0.1},
                    ],
                },
                "TestNamespace/Positioner01": {
                    "properties": [
                        {"name": "current", "timer": 0.1},
                    ]
                }
            }
            publisher = Publisher(config)
        """
        self.unavailable_components = {}
        r.delete('components')
        if len(args) == 0:
            pass
        elif len(args) == 1:  # The argument must be a dictionary (JSON format)
            self.add_jobs(*args)
        else:
            logger.error('Publisher takes 0 or 1 argument, %d given' % len(args))

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
            "TestNamespace/Positioner": {
                "properties": [
                    {
                        "name": "position",
                        "description": "actual position",
                        "timer": 0.1
                    }
                ],
                "methods": [
                    {
                        "name": "getPosition",
                        "description": "actual position",
                        "timer": 0.1
                    }
                ],
            }
        }
        """
        # list of tuples [(component, attribute_name, timer), (...)]
        pjobs_args = []  # Properties list
        mjobs_args = []  # Methods list
        from suricate.services import Component
        for component_name, targets in config.items():
            # Set the default redis values
            error_message = 'cannot get component %s' % component_name
            properties = targets.get('properties', [])
            methods = targets.get('methods', [])
            try:
                c = Component(component_name)
                # Remove the component from the unavailable dictionary
                self.unavailable_components.pop(component_name, None)
            except CannotGetComponentError:
                self.unavailable_components[component_name] = targets
                logger.error(error_message)
                
            for prop in properties:
                attr_name = prop['name']
                if component_name in self.unavailable_components:
                    self._set_attr_error(component_name, attr_name, error_message)
                else:
                    if hasattr(c, '_get_%s' % attr_name):
                        pjobs_args.append((c, attr_name, prop['timer']))
                    else:
                        logger.error('%s has not property %s' % (c.name, attr_name))

            for method in methods:
                attr_name = method['name']
                if component_name in self.unavailable_components:
                    self._set_attr_error(component_name, attr_name, error_message)
                else:
                    if hasattr(c, attr_name):
                        mjobs_args.append((c, attr_name, method['timer']))
                    else:
                        logger.error('%s has not method %s' % (c.name, attr_name))

        for arg in pjobs_args:
            self.s.add_attribute_job(*arg)

        for met in mjobs_args:
            self.s.add_attribute_job(*met)


    def rescheduler(self):
        # Check if unavailable components are now available
        for comp, status in r.hgetall('components').items():
            if status == 'available':
                self.unavailable_components.pop(comp, None)

        self.add_jobs(self.unavailable_components)

        scheduled_comps = set()
        # Reschedule old jobs currently unavailable
        for job in self.get_jobs():
            if job.id.count('/') == 2:
                component_name = '/'.join(job.id.split('/')[:2])
                scheduled_comps.add(component_name)
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

        # Create a set of unavailable components
        unavailable_comps = set()
        for comp in self.unavailable_components:
            unavailable_comps.add(comp)
        for comp, status in r.hgetall('components').items():
            if status == 'unavailable':
                unavailable_comps.add(comp)
            elif comp in unavailable_comps:
                unavailable_comps.remove(comp)
                

        all_comps = unavailable_comps | scheduled_comps
        for comp in all_comps:
            if comp in unavailable_comps:
                r.hmset('components', {comp: 'unavailable'})
            else:
                r.hmset('components', {comp: 'available'})


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
            if not r.get(error_job_key) and job:
                # Save job.seconds, because we will temporarily change it
                sec, mic = job.trigger.interval.seconds, job.trigger.interval.microseconds
                interval = sec + mic / (1.0 * 10 ** 6)
                if not r.set(error_job_key, interval):
                    logger.error('cannot set %s' % error_job_key)
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

    def _set_attr_error(self, component_name, attribute, message):
        data_dict = {
            'error': '',
            'value': '',
            'timestamp': str(datetime.datetime.utcnow())
        }
        job_id = '%s/%s' % (component_name, attribute)
        data_dict.update({'error': message})
        if not r.hmset(job_id, data_dict):
            logger.error('cannot write on redis: "%s"' % message)
        r.publish(job_id, json.dumps(data_dict))

