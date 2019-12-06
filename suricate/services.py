from suricate.errors import CannotGetComponentError


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

    def __init__(self, name):
        if not getManager():
            raise CannotGetComponentError('ACS not running')
        if name in self.unavailables:
            raise CannotGetComponentError('component %s not available' % name)
        self.name = str(name)
        if not hasattr(self, '_client'):
            from Acspy.Clients.SimpleClient import PySimpleClient
            self._client = PySimpleClient()
        try:
            self._component = self._client.getComponent(self.name)
        except Exception:
            # This except clause catches a omniORB.CORBA.OBJECT_NOT_EXISTS in case
            # the client has been disconnected.  It caches a CORBA.COMM_FAILURE
            # when the container is down and after that you call getComponent()
            # for the first time. If the container is still down and you call
            # getComponent() another time, than it catches omniORB.CORBA.TRANSIENT
            self._component = None
            raise CannotGetComponentError('component %s not available' % self.name)

    def __getattr__(self, name):
        # TODO: In case __init__ does not get the component,
        # self._component is None and getattr(self._component, name)
        # will rase an exception. To be fixed.
        attr = self.__dict__.get(name) or getattr(self._component, name)
        return Proxy(attr, self.name)

    def release(self):
        try:
            self._client.forceReleaseComponent(self.name)
        except:
            # TODO: log
            pass


def getManager():
    from Acspy.Util.ACSCorba import getManager as mng_ref
    return mng_ref()
