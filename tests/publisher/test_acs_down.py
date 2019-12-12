import pytest
import time
from suricate.configuration import config

import suricate.services


def test_startup(Publisher, redis_client):
    """ACS not running at startup."""
    try:
        suricate.services.is_manager_online = lambda: False  # Mock getManager
        p = Publisher(config['COMPONENTS'])
        p.start()
        time.sleep(config['SCHEDULER']['RESCHEDULE_ERROR_INTERVAL']*1.2)
        message = redis_client.hget('TestNamespace/Positioner00/position', 'error')
        value = redis_client.hget('TestNamespace/Positioner00/position', 'value')
        assert message == 'ACS not running'
        assert value == ''
        message = redis_client.hget('TestNamespace/Positioner00/getPosition', 'error')
        value = redis_client.hget('TestNamespace/Positioner00/getPosition', 'value')
        assert message == 'ACS not running'
        assert value == ''
        message = redis_client.hget('TestNamespace/Positioner01/current', 'error')
        value = redis_client.hget('TestNamespace/Positioner01/current', 'value')
        assert message == 'ACS not running'
        assert value == ''
        components = redis_client.hgetall('components')
        assert len(components) == 2
        for component, status in components.items():
            assert status == 'unavailable'
    finally:
        suricate.services.is_manager_online = lambda: True


def test_after_startup(Publisher, redis_client):
    """ACS not running after startup."""
    try:
        p = Publisher(config['COMPONENTS'])
        p.start()
        time.sleep(config['SCHEDULER']['RESCHEDULE_ERROR_INTERVAL']*1.2)
        message = redis_client.hget('TestNamespace/Positioner00/position', 'error')
        assert message == ''
        message = redis_client.hget('TestNamespace/Positioner00/getPosition', 'error')
        assert message == ''
        message = redis_client.hget('TestNamespace/Positioner01/current', 'error')
        assert message == ''
        components = redis_client.hgetall('components')
        assert len(components) == 2
        for component, status in components.items():
            assert status == 'available'

        # ACS not running
        for c in config['COMPONENTS']:
            suricate.component.Component.unavailables.append(c)
        suricate.services.is_manager_online = lambda: False
        time.sleep(config['SCHEDULER']['RESCHEDULE_ERROR_INTERVAL']*5)
        message = redis_client.hget('TestNamespace/Positioner00/position', 'error')
        assert message == 'ACS not running'
        message = redis_client.hget('TestNamespace/Positioner00/getPosition', 'error')
        assert message == 'ACS not running'
        message = redis_client.hget('TestNamespace/Positioner01/current', 'error')
        assert message == 'ACS not running'
        components = redis_client.hgetall('components')
        assert len(components) == 2
        for component, status in components.items():
            assert status == 'unavailable'

        # ACS running again
        suricate.services.is_manager_online = lambda: True
        suricate.component.Component.unavailables = []
        time.sleep(config['SCHEDULER']['RESCHEDULE_ERROR_INTERVAL']*2)
        message = redis_client.hget('TestNamespace/Positioner00/position', 'error')
        assert message == ''
        message = redis_client.hget('TestNamespace/Positioner00/getPosition', 'error')
        assert message == ''
        message = redis_client.hget('TestNamespace/Positioner01/current', 'error')
        assert message == ''
        components = redis_client.hgetall('components')
        assert len(components) == 2
        for component, status in components.items():
            assert status == 'available'
    finally:
        suricate.component.Component.unavailables = []
        suricate.services.is_manager_online = lambda: True


if __name__ == '__main__':
    pytest.main()
