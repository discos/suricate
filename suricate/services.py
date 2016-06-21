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

    def __init__(self, name):
        self.device_attribute_prefix = '_get_'
        self.name = str(name)
        if not hasattr(self, '_client'):
            from Acspy.Clients.SimpleClient import PySimpleClient
            self._client = PySimpleClient()
        try:
            self._component = self._client.getComponent(self.name)
        except Exception:
            raise CannotGetComponentError('%s not available' % self.name)

    def __del__(self):
        self._client.disconnect()

    def __getattr__(self, name):
        attr = self.__dict__.get(name) or getattr(self._component, name)
        return Proxy(attr, self.name)

    def release(self):
        try:
            self._client.forceReleaseComponent(self.name)
        except:
            pass
        finally:
            self.__del__()
