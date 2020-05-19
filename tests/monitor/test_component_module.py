"""This module tests the real component.py, just mocking the client"""
import pytest
import conftest
import time
import suricate.services
import suricate.component
from suricate.configuration import config
from suricate.errors import CannotGetComponentError 


COMP_NAME = 'TestNamespace/Positioner00'
CONT_NAME = 'PositionerContainer'
suricate.services.is_container_online = lambda x: True


def test_manager_offline():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    try:
        suricate.services.is_manager_online = lambda: False
        with pytest.raises(CannotGetComponentError):
            suricate.component.Component(COMP_NAME, CONT_NAME)
    finally:
        suricate.services.is_manager_online = lambda: True


def test_component_unavailable():
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    try:
        suricate.component.Component.unavailables.append('TestNamespace/Positioner00')
        with pytest.raises(CannotGetComponentError):
            suricate.component.Component(COMP_NAME, CONT_NAME)
    finally:
        suricate.component.Component.unavailables = []


def test_container_offline():
    """The container is offline, raise CannotGetComponentError"""
    # suricate.component has been moked, reload the original one
    reload(suricate.component)
    try:
        suricate.services.is_container_online = lambda x: False
        with pytest.raises(CannotGetComponentError):
            suricate.component.Component(COMP_NAME, CONT_NAME)
    finally:
        suricate.services.is_container_online = lambda x: True


def test_get_component():
    # suricate.component has been moked, reload the original one
    # Real component, mocked client
    reload(suricate.component)
    try:
        Client = suricate.services.get_client_class()
        conftest.MockACSClient.set_exc_name('CannotGetComponent')
        suricate.services.get_client_class = lambda: conftest.MockACSClient
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(COMP_NAME, CONT_NAME)
        expected = 'component %s not available' % COMP_NAME
        assert expected in str(exc.value)
    finally:
        suricate.services.get_client_class = lambda: Client
        conftest.MockACSClient.set_exc_name('')


def test_no_permission_ex():
    # suricate.component has been moked, reload the original one
    # Real component, mocked client
    reload(suricate.component)
    try:
        Client = suricate.services.get_client_class()
        conftest.MockACSClient.set_exc_name('NoPermissionEx')
        suricate.services.get_client_class = lambda: conftest.MockACSClient
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(COMP_NAME, CONT_NAME)
        expected = 'component %s not available' % COMP_NAME
        assert expected in str(exc.value)
    finally:
        suricate.services.get_client_class = lambda: Client
        conftest.MockACSClient.set_exc_name('')


def test_comm_failure_manager_online():
    # suricate.component has been moked, reload the original one
    # Real component, mocked client
    reload(suricate.component)
    try:
        Client = suricate.services.get_client_class()
        conftest.MockACSClient.set_exc_name('COMM_FAILURE')
        suricate.services.get_client_class = lambda: conftest.MockACSClient
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(COMP_NAME, CONT_NAME)
        expected = 'cannot communicate with component'
        assert expected in str(exc.value)
    finally:
        suricate.services.get_client_class = lambda: Client
        conftest.MockACSClient.set_exc_name('')


def test_comm_failure_manager_offline():
    # suricate.component has been moked, reload the original one
    # Real component, mocked client
    reload(suricate.component)
    try:
        Client = suricate.services.get_client_class()
        conftest.MockACSClient.set_exc_name('COMM_FAILURE')
        suricate.services.get_client_class = lambda: conftest.MockACSClient
        suricate.services.is_manager_online = lambda: False
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(COMP_NAME, CONT_NAME)
        expected = 'ACS not running'
        assert expected in str(exc.value)
    finally:
        suricate.services.get_client_class = lambda: Client
        suricate.services.is_manager_online = lambda: True
        conftest.MockACSClient.set_exc_name('')


def test_unexpected_exception_manager_online():
    # suricate.component has been moked, reload the original one
    # Real component, mocked client
    reload(suricate.component)
    try:
        Client = suricate.services.get_client_class()
        conftest.MockACSClient.set_exc_name('unexpected')
        suricate.services.get_client_class = lambda: conftest.MockACSClient
        with pytest.raises(CannotGetComponentError) as exc:
            suricate.component.Component(COMP_NAME, CONT_NAME)
        expected = 'component %s not available' % COMP_NAME
        assert expected in str(exc.value)
    finally:
        suricate.services.get_client_class = lambda: Client
        conftest.MockACSClient.set_exc_name('')


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
