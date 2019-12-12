import pytest
import time
import suricate.services
import suricate.component
from suricate.configuration import config
from suricate.errors import CannotGetComponentError 


class Client(object):

    def __init__(self):
        self.exc_name = ''

    def getComponent(self, name):
        class MyException(Exception): pass
        if self.exc_name:
            exc = MyException()
            exc.__class__.__name__ = self.exc_name
            raise exc

    def set_exc_name(self, exc_name):
        self.exc_name = exc_name


def test_manager_offline():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    try:
        suricate.services.is_manager_online = lambda: False
        with pytest.raises(CannotGetComponentError):
            suricate.component.Component('TestNamespace/Positioner00')
    finally:
        suricate.services.is_manager_online = lambda: True


def test_component_unavailable():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    try:
        suricate.component.Component.unavailables.append('TestNamespace/Positioner00')
        with pytest.raises(CannotGetComponentError):
            suricate.component.Component('TestNamespace/Positioner00')
    finally:
        suricate.component.Component.unavailables = []


def test_get_component():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    client = Client()
    client.set_exc_name('CannotGetComponent')
    try:
        suricate.component.Component._client = client
        comp_name = 'TestNamespace/Positioner00'
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(comp_name)
        expected = 'component %s not available' % comp_name
        assert expected in str(exc.value)
        assert suricate.component.Component._client
    finally:
        suricate.component.Component._client = None


def test_no_permission_ex():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    client = Client()
    client.set_exc_name('NoPermissionEx')
    try:
        suricate.component.Component._client = client
        comp_name = 'TestNamespace/Positioner00'
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(comp_name)
        expected = 'component %s not available' % comp_name
        assert expected in str(exc.value)
        assert suricate.component.Component._client is None
    finally:
        suricate.component.Component._client = None


def test_comm_failure_manager_online():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    client = Client()
    client.set_exc_name('COMM_FAILURE')
    try:
        suricate.component.Component._client = client
        comp_name = 'TestNamespace/Positioner00'
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(comp_name)
        expected = 'cannot communicate with component'
        assert expected in str(exc.value)
        assert suricate.component.Component._client
    finally:
        suricate.component.Component._client = None


def test_comm_failure_manager_offline():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    client = Client()
    client.set_exc_name('COMM_FAILURE')
    try:
        suricate.services.is_manager_online = lambda: False
        suricate.component.Component._client = client
        comp_name = 'TestNamespace/Positioner00'
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(comp_name)
        expected = 'ACS not running'
        assert expected in str(exc.value)
        assert suricate.component.Component._client
    finally:
        suricate.component.Component._client = None
        suricate.services.is_manager_online = lambda: True


def test_unexpected_exception_manager_online():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    client = Client()
    client.set_exc_name('unexpected')
    try:
        suricate.component.Component._client = client
        comp_name = 'TestNamespace/Positioner00'
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(comp_name)
        expected = 'component %s not available' % comp_name
        assert expected in str(exc.value)
        assert suricate.component.Component._client is None
    finally:
        suricate.component.Component._client = None
        suricate.services.is_manager_online = lambda: True


def test_proxy_attribute():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    my_object = 'a string'
    p = suricate.component.Proxy('text', my_object)
    assert p.upper() == 'TEXT'


def test_proxy_call():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    my_object = 'a string'
    p = suricate.component.Proxy('text', my_object)
    with pytest.raises(CannotGetComponentError) as exc:
        p()
    assert 'broken reference' in str(exc.value)



if __name__ == '__main__':
    pytest.main()
