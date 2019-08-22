import redis
from apscheduler import events

from suricate.schedulers import Scheduler
from suricate.errors import CannotGetComponentError, ComponentAttributeError


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
                        {"name": "position", "timer": 0.1},
                        {"name": "current", "timer": 0.1},
                    ],
                "TestNamespace/Positioner01":
                    [
                        {"name": "current", "timer": 0.1},
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
            self.add_jobs({comp: [{'name': attr, 'timer': timer}]})

        Publisher.add_errors_listener()

    def add_jobs(self, config):
        """
        {
            "TestNamespace/Positioner":
            [
                {
                    "name": "position",
                    "description": "actual position",
                    "timer": 0.1
                }
            ]
        }
        """
        args = []  # list of tuples [(component, attribute_name, timer), (...)]
        from suricate.services import Component
        for component_name, attributes in config.items():
            c = Component(component_name)
            prefix = c.device_attribute_prefix
            for a in attributes:
                if hasattr(c, prefix + a['name']):
                    args.append((c, a['name'], a['timer']))
                else:
                    raise ValueError(
                        '%s has not attribute %s' % (c.name, a['name']))

        for arg in args:
            self.s.add_attribute_job(*arg)

    def get_jobs(self):
        return self.s.get_jobs()

    @classmethod
    def add_errors_listener(cls):
        cls.s.add_listener(cls.errors_listener, events.EVENT_JOB_ERROR)

    @staticmethod
    def errors_listener(event):
        job_id = event.job_id
        if isinstance(
                event.exception,
                (CannotGetComponentError, ComponentAttributeError)):
            job = Publisher.s.get_job(job_id)
            r = redis.StrictRedis()
            job_key = 'job:%s' % job_id
            if not r.get(job_key):
                # Save job.seconds, because we will temporarily change it
                r.set(job_key, job.trigger.interval.seconds)
                # Slowdown the job, until the component comes available
                Publisher.s.reschedule_job(
                    job_id, trigger='interval', seconds=1)

            channel, old_component_ref, attribute = job.args
            from suricate.services import Component
            # If the component is available, we pass its reference to the job
            # and we restore the original job heartbeat
            try:
                component_ref = Component(old_component_ref.name)
                args = channel, component_ref, attribute
                Publisher.s.modify_job(job_id, args=args)
                sec = float(r.get(job_key))
                Publisher.s.reschedule_job(
                    job_id, trigger='interval', seconds=sec)
                r.delete(job_key)
            except CannotGetComponentError:
                pass  # Do nothing

    @classmethod
    def start(cls):
        cls.s.start()

    @classmethod
    def shutdown(cls):
        for job in cls.s.get_jobs():
            job.remove()
        cls.s.shutdown(wait=False)
        cls.s = Scheduler()
