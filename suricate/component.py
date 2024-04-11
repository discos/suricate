from datetime import datetime, timedelta
import redis
import suricate.services
from suricate.errors import CannotGetComponentError
from suricate.configuration import dt_format


r = redis.StrictRedis(decode_responses=True)
# Remove old status keys from the DB
for key in r.scan_iter("*"):
    if key.startswith('__'):
        r.delete(key)


class Proxy:

    def __init__(self, attr, comp_name):
        self._attr = attr
        self._comp_name = comp_name

    def __getattr__(self, name):
        return getattr(self._attr, name)

    def __call__(self, *args, **kwargs):
        try:
            return self._attr(*args, **kwargs)
        except Exception as ex:
            raise CannotGetComponentError(
                f'broken reference to {self._comp_name}') from ex


class Component:
    """Delegate the attribute access to an ACS component"""

    unavailables = []  # Unavailable components
    clients = {}

    def __init__(self, name, container, startup_delay=0):
        self.name = str(name)
        self.container = str(container)
        self.startup_delay = startup_delay

        if not suricate.services.is_manager_online():
            raise CannotGetComponentError('ACS not running')
        if name in self.unavailables:
            raise CannotGetComponentError(f'component {name} not available')
        try:
            with suricate.services.logging_lock:
                self.release()
                if not suricate.services.is_container_online(self.container):
                    raise CannotGetComponentError(f'{self.name} not running')
                Client = suricate.services.get_client_class()
                client = Client(self.name)
                Component.clients[self.name] = client
                self._component = \
                    Component.clients[self.name].getComponent(self.name)
                startup_time = \
                    datetime.utcnow() + timedelta(seconds=startup_delay)
                r.set(
                    f'__{self.name}/startup_time',
                    startup_time.strftime(dt_format),
                )
        except Exception as ex:
            # I check the name of the class because I can not catch the
            # proper exception. Actually I can not catch it when executing
            # the tests online, where there is either no ACS no CORBA.
            message = str(ex)
            ex_name = ex.__class__.__name__
            if 'CannotGetComponent' in ex_name:
                # ACS is running, component not available
                message = f'component {self.name} not available'
            elif 'NoPermissionEx' in ex_name:
                # ACS has been shutdown after the client instantiation. Now
                # it is available again but the client is no more active and
                # has to be istantiated
                message = f'component {self.name} not available'
            elif 'COMM_FAILURE' in ex_name or 'TRANSIENT' in ex_name:
                # ACS is not running: do not istantiate a new client
                if not suricate.services.is_manager_online():
                    message = 'ACS not running'
                else:
                    message = f'cannot communicate with component {self.name}'
            else:  # Online tests
                if not suricate.services.is_manager_online():
                    message = 'ACS not running'
                else:
                    message = f'component {self.name} not available'
            raise CannotGetComponentError(message) from ex

    def __getattr__(self, name):
        # TODO: In case __init__ does not get the component,
        # self._component is None and getattr(self._component, name)
        # will rase an exception. To be fixed.
        attr = self.__dict__.get(name) or getattr(self._component, name)
        return Proxy(attr, self.name)

    def release(self):
        client = Component.clients.pop(self.name, None)
        if client:
            client.forceReleaseComponent(self.name)
            client.disconnect()
