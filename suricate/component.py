import logging
import threading
import suricate.services
from suricate.errors import CannotGetComponentError


logger = logging.getLogger('suricate')


class Proxy(object):

    def __init__(self, attr, comp_name):
        self._attr = attr
        self._comp_name = comp_name

    def __getattr__(self, name):
        return getattr(self._attr, name)

    def __call__(self, *args, **kwargs):
        try:
            return self._attr(*args, **kwargs)
        except Exception:
            raise CannotGetComponentError(
                'broken reference to %s' % self._comp_name)


class Component(object):
    """Delegate the attribute access to an ACS component"""

    unavailables = []  # Unavailable components
    clients = {}
    lock = threading.Lock()

    def __init__(self, name, container):
        self.name = str(name)
        self.container = str(container)

        if not suricate.services.is_manager_online():
            raise CannotGetComponentError('ACS not running')
        if name in self.unavailables:
            raise CannotGetComponentError('component %s not available' % name)
        try:
            with Component.lock:
                self.release()
                try:
                    is_online = True
                    is_online = suricate.services.is_container_online(self.container)
                except Exception, ex:
                    # In case of exception I do not know if the container is offline
                    # or online, so I suppose it is online and I get a new client
                    logger.warning('cannot get the %s status' % self.container)

                if not is_online:
                    raise CannotGetComponentError('%s container not running' % self.name)
                else:
                    Client = suricate.services.get_client_class()
                    client = Client(self.name)
                    Component.clients[self.name] = client
                    self._component = Component.clients[self.name].getComponent(self.name)
        except Exception, ex:
            # I check the name of the class because I can not catch the
            # proper exception. Actually I can not catch it when executing
            # the tests online, where there is either no ACS no CORBA.
            message = str(ex)
            ex_name = ex.__class__.__name__
            if 'CannotGetComponent' in ex_name:
                # ACS is running, component not available
                message = 'component %s not available' % self.name
            elif 'NoPermissionEx' in ex_name:
                # ACS has been shutdown after the client instantiation. Now
                # it is available again but the client is no more active and
                # has to be istantiated
                message = 'component %s not available' % self.name
            elif 'COMM_FAILURE' in ex_name or 'TRANSIENT' in ex_name:
                # ACS is not running: do not istantiate a new client
                if not suricate.services.is_manager_online():
                    message = 'ACS not running'
                else:
                    message = 'cannot communicate with component %s' % self.name
            else:  # Online tests
                if not suricate.services.is_manager_online():
                    message = 'ACS not running'
                else:
                    message = 'component %s not available' % self.name
            raise CannotGetComponentError(message)


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
