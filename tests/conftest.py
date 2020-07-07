import time
import logging
import threading
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta
from pytz import utc

import pytest
import redis
import rq
from flask import current_app
from flask.testing import FlaskClient
from suricate.api import create_app, db

import suricate.services
from suricate.errors import CannotGetComponentError
from suricate.configuration import formatter, dt_format
from suricate.monitor.core import Publisher as Publisher_
from suricate.dbfiller import DBFiller
from suricate.monitor.schedulers import Scheduler
from suricate.server import start_publisher, stop_publisher

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.schedulers import SchedulerNotRunningError


def pytest_addoption(parser):
    parser.addoption(
        "--acs",
        action="store_true",
        help="Execute the tests on real ACS components"
)


def pytest_cmdline_main(config):
    if config.getoption('--acs'):
        print '\nRunning the test with ACS'
    else:
        print '\nRunning the test with mock components'


@pytest.fixture(autouse=True)
def mock_objects(request, monkeypatch):
    """Mock suricate.services when --acs is not given"""
    if not request.config.getoption('--acs'):
        monkeypatch.setattr('suricate.component.Component', MockComponent)
        monkeypatch.setattr('suricate.services.get_client_class', lambda: MockACSClient)
        monkeypatch.setattr('suricate.services.is_manager_online', lambda: True)
        monkeypatch.setattr('suricate.services.is_container_online', lambda x: True)


@pytest.fixture(autouse=True)
def logger(request):
    r = redis.StrictRedis()
    # Log messages start with ___ : remove them
    for key in r.scan_iter("*"):
        if key.startswith('__'):
            r.delete(key)
    f = NamedTemporaryFile()
    file_handler = logging.FileHandler(f.name, 'w')
    file_handler.setFormatter(formatter)
    logger = logging.getLogger('suricate')
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    logger.addHandler(file_handler)
    def close_tmpfile():
        f.close()
    request.addfinalizer(close_tmpfile)
    logger.file_name = f.name
    return logger


@pytest.fixture
def client():
    """Flask client used to test the REST API"""

    class AppClient(FlaskClient):

        def __init__(self, *args, **kwargs):
            super(self.__class__, self).__init__(*args, **kwargs)

        def __enter__(self):
            db.create_all()
            start_publisher()
            super(self.__class__, self).__enter__()
            return self

        def __exit__(self, exc_type, exc_value, tb):
            stop_publisher()
            db.session.commit()
            db.session.remove()
            db.drop_all()
            db.create_all()
            super(self.__class__, self).__exit__(exc_type, exc_value, tb)

    app = create_app('testing')
    app_context = app.app_context()
    app_context.push()
    app.test_client_class = AppClient
    with app.test_client() as test_client:
        test_client.testing = True
        return test_client


@pytest.fixture()
def Publisher(request):

    def shutdown():
        try:
            Publisher_.shutdown()
            print '\nShutting down the scheduler...'
            time.sleep(1)
        except SchedulerNotRunningError:
            pass

    request.addfinalizer(shutdown)
    return Publisher_


@pytest.fixture()
def dbfiller(request):

    def shutdown():
        DBFiller.shutdown()
        print '\nShutting down the dbfiller...'
        time.sleep(1)

    request.addfinalizer(shutdown)
    return DBFiller()


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
        max_time = datetime.utcnow() + timedelta(seconds=timeout)
        while datetime.utcnow() < max_time:
            message = self._pubsub.get_message()
            if message and message['type'] == 'pmessage':
                return message  # From str to dict
            time.sleep(0.0001)


class MockACSClient(object):
    """Fake ACS PySimpleClient, to use when ACS is not active"""
    
    exc_name = ''

    def __init__(self, client_name):
        client_name = client_name

    def getComponent(self, component_name):
        class MyException(Exception): pass
        if self.exc_name:
            exc = MyException()
            exc.__class__.__name__ = self.exc_name
            raise exc

    @classmethod
    def set_exc_name(cls, exc_name):
        cls.exc_name = exc_name
    
    def forceReleaseComponent(self, name):
        pass

    def disconnect(self):
        pass


class MockComponent(object):
    """Fake suricate.component.Component, to use when ACS is not active"""

    components = {}
    unavailables = []  # Unavailable components
    clients = {}
    lock = threading.Lock()

    properties = {
        'position': 0,
        'current': 1,
        'seq': (1.1, 2.3, 3.3)
    }

    def __new__(cls, name, container, startup_delay):
        if name in cls.unavailables:
            raise CannotGetComponentError('%s unavailable' % name)
        if name not in cls.components:
            cls.components.update(
                {name: super(MockComponent, cls).__new__(cls)})
            with MockComponent.lock:
                MockComponent.clients[name] = True
        return cls.components[name]

    def __init__(
            self,
            name='TestNamespace/MyComponent',
            container='PositionerContainer',
            startup_delay=0
        ):
        if not suricate.services.is_manager_online():
            raise CannotGetComponentError('ACS not running')
        if name in self.unavailables:
            raise CannotGetComponentError('component %s not available' % name)

        self.name = name
        self.container = container
        self.startup_delay = int(startup_delay)
        startup_time = datetime.utcnow() + timedelta(seconds=self.startup_delay)
        r = redis.StrictRedis()
        r.set(
            '__%s/startup_time' % self.name,
            startup_time.strftime(dt_format),
        )
        for property_ in MockComponent.properties.items():
            self.set_property(*property_)

    def release(self):
        def get_sync():
            raise CannotGetComponentError('broken reference')

        for name in MockComponent.properties:
            property_ = getattr(self, '_get_%s' % name)()
            property_.get_sync = get_sync

        with MockComponent.lock:
            MockComponent.clients.pop(self.name, None)

        if self.name in self.__class__.components:
            del self.__class__.components[self.name]

    def setPosition(self, value):
        self.set_property('position', value)

    def setSequence(self, value):
        self.set_property('seq', value)

    def _property_value(self, property_):
        obj = property_()
        comp = property_.get_sync()
        value, timestamp = comp
        return value

    def getPosition(self):
        if not suricate.services.is_manager_online():
            raise CannotGetComponentError('ACS not running')
        else:
            return self._property_value(self._get_position)

    def getCurrent(self):
        if not suricate.services.is_manager_online():
            raise CannotGetComponentError('ACS not running')
        else:
            return self._property_value(self._get_current)

    def getSequence(self):
        if not suricate.services.is_manager_online():
            raise CannotGetComponentError('ACS not running')
        else:
            return self._property_value(self._get_seq)

    def command(self, line):
        cmd = line.strip()
        if cmd == 'getTpi':
            return True, 'getTpi\\\n00) 800.3\n01) 750.7'
        else:
            if '=' in cmd:
                cmd = cmd.split('=')[0]
            return False, '%s? ...' % cmd

    def set_property(
            self,
            name,
            value,
            error_code=0,
            timestamp=138129971470735140L,
        ):
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
        if not suricate.services.is_manager_online():
            raise CannotGetComponentError('ACS not running')
        else:
            return (self.value, self.completion)

    def __call__(self):
        if not suricate.services.is_manager_online():
            raise CannotGetComponentError('ACS not running')
        else:
            return self


class Completion(object):
    def __init__(self, code=0, timestamp=138129971470735140L):
        self.code = code
        self.timeStamp = timestamp


def Component():
    """Return an ACS component class or a MockComponent"""
    import suricate.component
    return suricate.component.Component


@pytest.fixture()
def component(request, component_id=0):
    """Return a Positioner instance.

    The parameter component_id is the component identifier. That means
    to default it gets and returns the TestNamespace/Positioner00 component.
    """
    ComponentClass = Component()
    comp = ComponentClass(
        'TestNamespace/Positioner%02d' % component_id,
        'PositionerContainer',
         0 # secondos of startup_delay
    )

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
        comp = ComponentClass(
            'TestNamespace/Positioner%02d' % i,
            'PositionerContainer',
             0 # secondos of startup_delay
        )
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
def redis_client(request):
    r = redis.StrictRedis()

    def close_redis_client():
        r.flushall()
        r.close()

    request.addfinalizer(close_redis_client)
    return r


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
        max_time = datetime.utcnow() + timedelta(seconds=timeout)
        while datetime.utcnow() < max_time:
            if job.pending:
                time.sleep(job.trigger.interval.seconds)

        if job.pending:
            raise Exception("Error: job %s pending" % job)

    s.wait_until_executed = wait_until_executed

    def shutdown():
        s.shutdown()

    request.addfinalizer(shutdown)
    return s
