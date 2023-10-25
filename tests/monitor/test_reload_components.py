import pytest
import time
import json
import suricate.component
from mock import patch, mock_open
import importlib


def get_user_config(startup_delay=0):
    return """
COMPONENTS:
  TestNamespace/Positioner02:
    startup_delay: %d
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
    startup_delay: %d
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
  dbfiller_cycle: 1
DATABASE: testing
RUN_ON_MANAGER_HOST: True
""" % (startup_delay, startup_delay)



def test_startup_delay(Publisher, redis_client, logger):
    """The component will be active after startup_delay"""
    try:  # Load the user configuration
        startup_delay =  3 # seconds
        user_config = get_user_config(startup_delay)
        from suricate import configuration
        func = "suricate.configuration.open"
        with patch(func, mock_open(read_data=user_config)) as f:
            importlib.reload(configuration)
            f.assert_called_with(configuration.config_file)
            from suricate.configuration import config

        p = Publisher(config['COMPONENTS'])
        p.start()
        time.sleep(2)
        # Components not available before startup_delay
        message = redis_client.hget('TestNamespace/Positioner02/position', 'error')
        assert message.endswith('startup in progress')
        message = redis_client.hget('TestNamespace/Positioner02/current', 'error')
        assert message.endswith('startup in progress')
        message = redis_client.hget('TestNamespace/Positioner02/getPosition', 'error')
        assert message.endswith('startup in progress')
        message = redis_client.hget('TestNamespace/Positioner03/current', 'error')
        assert message.endswith('startup in progress')

        time.sleep(startup_delay*5)  # Wait for the startup to terminate

        message = redis_client.hget('TestNamespace/Positioner00/position', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner00/current', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner00/getPosition', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner01/current', 'error')
        assert not message

        lines = open(logger.file_name).readlines()
        assert len(lines) == 4
        assert 'startup in progress' in lines[0]  # First component startup
        assert 'startup in progress' in lines[1]  # Second component startup
        assert 'is online' in lines[2]  # First component online
        assert 'is online' in lines[3]  # Second component online

    finally:
        importlib.reload(configuration)


def test_all_components_not_active_at_startup(Publisher, redis_client):
    """In case all components are not available at suricate startup,
    they have to be loaded as soon as they become available."""
    try:  # Load the user configuration
        user_config = get_user_config()
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
        message = redis_client.hget('TestNamespace/Positioner02/position', 'error')
        assert message == 'cannot get component TestNamespace/Positioner02'
        message = redis_client.hget('TestNamespace/Positioner02/current', 'error')
        assert message == 'cannot get component TestNamespace/Positioner02'
        message = redis_client.hget('TestNamespace/Positioner02/getPosition', 'error')
        assert message == 'cannot get component TestNamespace/Positioner02'
        message = redis_client.hget('TestNamespace/Positioner03/current', 'error')
        assert message == 'cannot get component TestNamespace/Positioner03'

        # Components available after starting the scheduler
        suricate.component.Component.unavailables = []
        p.start()
        waiting_time = 3 * config['SCHEDULER']['reschedule_interval']
        time.sleep(waiting_time)
        message = redis_client.hget('TestNamespace/Positioner00/position', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner00/current', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner00/getPosition', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner01/current', 'error')
        assert not message
    finally:
        suricate.component.Component.unavailables = []
        importlib.reload(configuration)


def test_some_components_not_active_at_startup(Publisher, redis_client):
    """In case some components are not available at suricate startup,
    they have to be loaded as soon as they become available."""
    try:  # Load the user configuration
        user_config = get_user_config()
        from suricate import configuration
        func = "suricate.configuration.open"
        with patch(func, mock_open(read_data=user_config)) as f:
            importlib.reload(configuration)
            f.assert_called_with(configuration.config_file)
            from suricate.configuration import config

        # Components not available before starting the scheduler
        suricate.component.Component.unavailables.append('TestNamespace/Positioner03')
        p = Publisher(config['COMPONENTS'])
        message = redis_client.hget('TestNamespace/Positioner02/position', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner02/current', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner02/getPosition', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner03/current', 'error')
        assert message == 'cannot get component TestNamespace/Positioner03'

        # Components available after starting the scheduler
        suricate.component.Component.unavailables = []
        p.start()
        waiting_time = 3 * config['SCHEDULER']['reschedule_interval']
        time.sleep(waiting_time)
        message = redis_client.hget('TestNamespace/Positioner00/position', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner00/current', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner00/getPosition', 'error')
        assert not message
        message = redis_client.hget('TestNamespace/Positioner01/current', 'error')
        assert not message
    finally:
        suricate.component.Component.unavailables = []
        importlib.reload(configuration)


if __name__ == '__main__':
    pytest.main()
