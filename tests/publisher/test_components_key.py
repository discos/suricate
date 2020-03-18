import pytest
import time
import json
import suricate.component
from mock import patch, mock_open


user_config = """
COMPONENTS:
  TestNamespace/Positioner01:
    methods:
    - name: getPosition
      timer: 0.1
    properties:
    - name: position
      timer: 0.1
  TestNamespace/Positioner02:
    methods:
    - name: getPosition
      timer: 0.1
    properties:
    - name: position
      timer: 0.1
    - name: current
      timer: 0.1
  TestNamespace/Positioner03:
    properties:
    - name: current
      timer: 0.1
HTTP:
  baseurl: http://127.0.0.1
  port: 5000
SCHEDULER:
  RESCHEDULE_ERROR_INTERVAL: 0.4
  RESCHEDULE_INTERVAL: 0.2
"""

startup_time = 5  # Seconds

def test_all_components_unavailable(Publisher, redis_client):
    try:  # Load the user configuration
        from suricate import configuration
        func = "suricate.configuration.open"
        with patch(func, mock_open(read_data=user_config)) as f:
            reload(configuration)
            f.assert_called_with(configuration.config_file)
            from suricate.configuration import config

        # Components not available before starting the scheduler
        for c in config['COMPONENTS']:
            suricate.component.Component.unavailables.append(c)
        p = Publisher(config['COMPONENTS'])
        p.start()
        time.sleep(startup_time)
        waiting_time = 3 * config['SCHEDULER']['RESCHEDULE_INTERVAL']
        time.sleep(waiting_time)
        components = redis_client.hgetall('components')
        assert len(components) == 3
        assert components['TestNamespace/Positioner01'] == 'unavailable'
        assert components['TestNamespace/Positioner02'] == 'unavailable'
        assert components['TestNamespace/Positioner03'] == 'unavailable'
    finally:
        suricate.component.Component.unavailables = []
        reload(configuration)


def test_all_components_available(Publisher, redis_client):
    try:  # Load the user configuration
        from suricate import configuration
        func = "suricate.configuration.open"
        with patch(func, mock_open(read_data=user_config)) as f:
            reload(configuration)
            f.assert_called_with(configuration.config_file)
            from suricate.configuration import config

        p = Publisher(config['COMPONENTS'])
        p.start()
        time.sleep(startup_time)
        waiting_time = 3 * config['SCHEDULER']['RESCHEDULE_INTERVAL']
        time.sleep(waiting_time)
        components = redis_client.hgetall('components')
        assert len(components) == 3
        assert components['TestNamespace/Positioner01'] == 'available'
        assert components['TestNamespace/Positioner02'] == 'available'
        assert components['TestNamespace/Positioner03'] == 'available'
    finally:
        suricate.component.Component.unavailables = []
        reload(configuration)


def test_some_components_unavailable(Publisher, redis_client):
    try:  # Load the user configuration
        from suricate import configuration
        func = "suricate.configuration.open"
        with patch(func, mock_open(read_data=user_config)) as f:
            reload(configuration)
            f.assert_called_with(configuration.config_file)
            from suricate.configuration import config

        # Components not available before starting the scheduler
        suricate.component.Component.unavailables.append(
            'TestNamespace/Positioner02'
        )
        p = Publisher(config['COMPONENTS'])
        p.start()
        time.sleep(startup_time)
        waiting_time = 3 * config['SCHEDULER']['RESCHEDULE_INTERVAL']
        time.sleep(waiting_time)
        components = redis_client.hgetall('components')
        assert len(components) == 3
        assert components['TestNamespace/Positioner01'] == 'available'
        assert components['TestNamespace/Positioner02'] == 'unavailable'
        assert components['TestNamespace/Positioner03'] == 'available'
        suricate.component.Component.unavailables.remove(
            'TestNamespace/Positioner02'
        )
        time.sleep(startup_time)
        time.sleep(waiting_time)
        components = redis_client.hgetall('components')
        assert len(components) == 3
        assert components['TestNamespace/Positioner01'] == 'available'
        assert components['TestNamespace/Positioner02'] == 'available'
        assert components['TestNamespace/Positioner03'] == 'available'
        suricate.component.Component.unavailables.append(
            'TestNamespace/Positioner01'
        )
        time.sleep(startup_time)
        time.sleep(waiting_time)
        components = redis_client.hgetall('components')
        assert len(components) == 3
        assert components['TestNamespace/Positioner01'] == 'unavailable'
        assert components['TestNamespace/Positioner02'] == 'available'
        assert components['TestNamespace/Positioner03'] == 'available'
    finally:
        suricate.component.Component.unavailables = []
        reload(configuration)


if __name__ == '__main__':
    pytest.main()
