import time
from datetime import datetime, timedelta
from pytz import utc

import pytest
import redis
from flask.testing import FlaskClient

from suricate.schedulers import Scheduler
from suricate.errors import CannotGetComponentError

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers import SchedulerNotRunningError


def pytest_addoption(parser):
    parser.addoption("--acs", action="store_true", help="ACS required")


def pytest_cmdline_main(config):
    if config.getoption('--acs'):
        print '\nRunning the test with ACS'
    else:
        print '\nRunning the test with mock components'


@pytest.fixture(autouse=True)
def mock_services(request, monkeypatch):
    """Mock suricate.services when --acs is not given"""
    if not request.config.getoption('--acs'):
        monkeypatch.setattr('suricate.services.Component', MockComponent)


@pytest.fixture
def client():
    from suricate.server import app, start

    class AppClient(FlaskClient):

        def __init__(self, *args, **kwargs):
            super(self.__class__, self).__init__(*args, **kwargs)

        def __enter__(self):
            start(run_app=False)
            super(self.__class__, self).__enter__()
            return self

        def __exit__(self, exc_type, exc_value, tb):
            # After executing start(), I can import publisher
            from suricate.server import publisher
            publisher.shutdown()
            super(self.__class__, self).__exit__(exc_type, exc_value, tb)

    app.test_client_class = AppClient
    with app.test_client() as test_client:
        test_client.testing = True
        return test_client


@pytest.fixture()
def Component():
    """Return an ACS component class or a MockComponent"""
    from suricate.services import Component as ComponentClass
    return ComponentClass


@pytest.fixture()
def Publisher(request):
    from suricate.core import Publisher as Pub

    def shutdown():
        try:
            Pub.shutdown()
        except SchedulerNotRunningError:
            pass

    request.addfinalizer(shutdown)
    return Pub


class RedisPubSub(object):
    """Delegate to a redis pubsub channel"""

    def __init__(self):
        self._redis = redis.StrictRedis()
        self._redis.flushall()
        self._pubsub = self._redis.pubsub()

    def __getattr__(self, name):
        return getattr(self._pubsub, name)

    def get_data_message(self, channel, timeout=2):
        """Get a message from a redis channel"""
        if channel not in self._pubsub.patterns:
            self._pubsub.psubscribe(channel)
        max_time = datetime.now() + timedelta(seconds=timeout)
        while datetime.now() < max_time:
            message = self._pubsub.get_message()
            if message and message['type'] == 'pmessage':
                return message  # From str to dict
            time.sleep(0.0001)


class MockComponent(object):
    """Fake ascpub.services.Component, to use when ACS is not active"""

    components = {}
    unavailables = ['foo']

    properties = {
        'position': 0,
        'current': 1,
    }

    def __new__(cls, name):
        if name in cls.unavailables:
            raise CannotGetComponentError('%s unavailable' % name)
        if name not in cls.components:
            cls.components.update(
                {name: super(MockComponent, cls).__new__(cls)})
        return cls.components[name]

    def __init__(self, name='TestNamespace/MyComponent'):
        self.name = name
        self.device_attribute_prefix = '_get_'
        for property_ in MockComponent.properties.items():
            self.set_property(*property_)

    def release(self):
        def get_sync():
            raise CannotGetComponentError('broken reference')

        for name in MockComponent.properties:
            property_ = getattr(self, '_get_%s' % name)()
            property_.get_sync = get_sync

        if self.name in self.__class__.components:
            del self.__class__.components[self.name]

    def setPosition(self, value):
        self.set_property('position', value)

    def set_property(self, name, value, error_code=0, timestamp=0):
        completion = Completion(error_code, timestamp)
        property_ = Property(name, value, completion)
        setattr(self, '_get_%s' % name, property_)

    def _get_name(self):
        return self.name


class Property(object):
    def __init__(self, name, value, completion):
        self.value = value
        self.completion = completion
        self.__name__ = '_get_%s' % name

    def setValue(self, value):
        self.value = value

    def get_sync(self):
        return (self.value, self.completion)

    def __call__(self):
        return self


class Completion(object):
    def __init__(self, code=0, timestamp=0):
        self.code = code
        self.timeStamp = timestamp


@pytest.fixture()
def component(request, component_id=0):
    """Return a Positioner instance.

    The parameter component_id is the component identifier. That means
    to default it gets and returns the TestNamespace/Positioner00 component.
    """
    ComponentClass = Component()
    comp = ComponentClass('TestNamespace/Positioner%02d' % component_id)

    def release():
        comp.release()

    request.addfinalizer(release)
    return comp


@pytest.fixture()
def components(request):
    """Return a list of Positioner instances"""
    comps = []
    ComponentClass = Component()
    for i in range(4):  # Get 4 components
        comp = ComponentClass('TestNamespace/Positioner%02d' % i)
        comps.append(comp)

    def release():
        for comp in comps:
            comp.release()

    request.addfinalizer(release)
    return comps


@pytest.fixture()
def pubsub(request):
    ps = RedisPubSub()

    def close_pubsub():
        ps.close()

    request.addfinalizer(close_pubsub)
    return ps


@pytest.fixture()
def scheduler(request):
    executors = {
        'default': ThreadPoolExecutor(10),
        'processpool': ProcessPoolExecutor(100)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 1
    }
    s = Scheduler(executors=executors, job_defaults=job_defaults, timezone=utc)
    s.start()

    def wait_until_executed(job, n=5):
        """Wait until the job is executed or n*job.trigger.interval.seconds"""
        timeout = n*job.trigger.interval.seconds
        max_time = datetime.now() + timedelta(seconds=timeout)
        while datetime.now() < max_time:
            if job.pending:
                time.sleep(job.trigger.interval.seconds)

        if job.pending:
            raise Exception("Error: job %s pending" % job)

    s.wait_until_executed = wait_until_executed

    def shutdown():
        s.shutdown()

    request.addfinalizer(shutdown)
    return s
