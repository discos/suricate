import pytest
import suricate.component


def test_zero_argument_init(Publisher):
    publisher = Publisher()
    jobs_id = [job.id for job in publisher.get_jobs()]
    assert jobs_id == ['rescheduler']


def test_one_argument_init(Publisher):
    """In case of only one argument, the Publisher expects a dictionary"""
    config = {
        "TestNamespace/Positioner00": {
            "container": "PositionerContainer",
            'properties': [
                {"name": "position", "timer": 0.1},
                {"name": "current", "timer": 0.1},
            ],
        },
        "TestNamespace/Positioner01": {
            "container": "PositionerContainer",
            'methods': [
                {"name": "getPosition", "timer": 0.1},
            ]
        }
    }
    publisher = Publisher(config)
    jobs_id = sorted([job.id for job in publisher.get_jobs()])
    assert jobs_id == [
        'TestNamespace/Positioner00/current',
        'TestNamespace/Positioner00/position',
        'TestNamespace/Positioner01/getPosition',
        'rescheduler',
    ]


def test_zero_arguments_init(Publisher):
    """In case of zero arguments there is only the rescheduler."""
    publisher = Publisher(1, 2, 3)
    jobs_id = [job.id for job in publisher.get_jobs()]
    assert jobs_id == ['rescheduler']


def test_wrong_number_arguments(Publisher, logger):
    """In case of wrong component name, write log message"""
    Publisher('foo', 'position', 0.1)
    line = open(logger.file_name).readline()
    assert 'ERROR' in line
    assert 'Publisher takes 0 or 1' in line


def test_wrong_component_name(Publisher, logger):
    """In case of wrong component name, write a log message"""
    try:
        config = {
            "foo": {
                "container": "PositionerContainer",
                "properties": [{"name": "current", "timer": 0.1}]
            }
        }
        suricate.component.Component.unavailables.append('foo')
        Publisher(config)
        line = open(logger.file_name).readline()
        assert 'ERROR' in line
        assert 'cannot get component foo' in line
    finally:
        suricate.component.Component.unavailables = []


def test_wrong_property_name(Publisher, logger):
    """In case of wrong property name, write log message"""
    config = {
        "TestNamespace/Positioner": {
            "container": "PositionerContainer",
            "properties": [
                {"name": "foo", "timer": 0.1}
            ]
        }
    }
    Publisher(config)
    line = open(logger.file_name).readline()
    assert 'ERROR' in line
    assert 'Positioner has not property foo' in line


if __name__ == '__main__':
    pytest.main()
