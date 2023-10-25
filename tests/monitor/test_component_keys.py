import pytest
import time
import json
import suricate.component
from mock import patch, mock_open
import importlib


user_config = """
COMPONENTS:
  TestNamespace/Positioner01:
    startup_delay: 0
    container: PositionerContainer
    methods:
    - name: getPosition
      timer: 0.2
    properties:
    - name: position
      timer: 0.2
  TestNamespace/Positioner02:
    startup_delay: 0
    container: PositionerContainer
    methods:
    - name: getPosition
      timer: 0.2
    properties:
    - name: position
      timer: 0.2
    - name: current
      timer: 0.2
  TestNamespace/Positioner03:
    startup_delay: 0
    container: PositionerContainer
    properties:
    - name: current
      timer: 0.2
HTTP:
  baseurl: http://127.0.0.1
  port: 5000
SCHEDULER:
  reschedule_error_interval: 0.4
  reschedule_interval: 0.2
"""

startup_time = 5  # Seconds

def test_all_components_unavailable(Publisher, redis_client):
    try:  # Load the user configuration
        from suricate import configuration
        func = "suricate.configuration.open"
        with patch(func, mock_open(read_data=user_config)) as f:
            importlib.reload(configuration)
            f.assert_called_with(configuration.config_file)
            from suricate.configuration import config

        # Components not available before starting the scheduler
        for c in config['COMPONENTS']:
            suricate.component.Component.unavailables.append(c)
        p = Publisher(config['COMPONENTS'])
        p.start()
        time.sleep(startup_time)
        waiting_time = 3 * config['SCHEDULER']['reschedule_interval']
        time.sleep(waiting_time)
        components = redis_client.hgetall('components')
        assert len(components) == 3
        assert components['TestNamespace/Positioner01'] == 'unavailable'
        assert components['TestNamespace/Positioner02'] == 'unavailable'
        assert components['TestNamespace/Positioner03'] == 'unavailable'
    finally:
        suricate.component.Component.unavailables = []
        importlib.reload(configuration)


def test_all_components_available(Publisher, redis_client):
    try:  # Load the user configuration
        from suricate import configuration
        func = "suricate.configuration.open"
        with patch(func, mock_open(read_data=user_config)) as f:
            importlib.reload(configuration)
            f.assert_called_with(configuration.config_file)
            from suricate.configuration import config

        p = Publisher(config['COMPONENTS'])
        p.start()
        time.sleep(startup_time)
        waiting_time = 3 * config['SCHEDULER']['reschedule_interval']
        time.sleep(waiting_time)
        components = redis_client.hgetall('components')
        assert len(components) == 3
        assert components['TestNamespace/Positioner01'] == 'available'
        assert components['TestNamespace/Positioner02'] == 'available'
        assert components['TestNamespace/Positioner03'] == 'available'
    finally:
        suricate.component.Component.unavailables = []
        importlib.reload(configuration)


def test_some_components_unavailable(Publisher, redis_client):
    try:  # Load the user configuration
        from suricate import configuration
        func = "suricate.configuration.open"
        with patch(func, mock_open(read_data=user_config)) as f:
            importlib.reload(configuration)
            f.assert_called_with(configuration.config_file)
            from suricate.configuration import config

        # Components not available before starting the scheduler
        suricate.component.Component.unavailables.append(
            'TestNamespace/Positioner02'
        )
        p = Publisher(config['COMPONENTS'])
        p.start()
        time.sleep(startup_time)
        waiting_time = 3 * config['SCHEDULER']['reschedule_interval']
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
        importlib.reload(configuration)


if __name__ == '__main__':
    pytest.main()
