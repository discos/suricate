import pytest
import time
from suricate.configuration import config
from mock import patch

import suricate.services
_getManager = suricate.services.getManager


def test_startup(Publisher, redis_client):
    """ACS not running at startup."""
    try:
        suricate.services.getManager = lambda: None  # Mock getManager
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
        suricate.services.getManager = _getManager


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
        suricate.services.getManager = lambda: None  # Mock getManager
        time.sleep(config['SCHEDULER']['RESCHEDULE_ERROR_INTERVAL']*1.2)
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
        suricate.services.getManager = lambda: 'running'
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
        suricate.services.getManager = _getManager


if __name__ == '__main__':
    pytest.main()
