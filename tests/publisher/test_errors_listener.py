"""Errors notified to the listener"""
import time
import json
import pytest
from suricate.configuration import config


def test_reload_component(Publisher, component, pubsub):
    """Docstring"""
    Publisher.add_errors_listener()
    Publisher.s.add_attribute_job(component, 'position', seconds=0.1)
    component.release()
    Publisher.start()
    message = pubsub.get_data_message(channel='*position')
    property_ = json.loads(message['data'])
    assert property_['error']  # Component not available
    time.sleep(config['SCHEDULER']['RESCHEDULE_ERROR_INTERVAL'] * 1.1)
    message = pubsub.get_data_message(channel='*position')
    property_ = json.loads(message['data'])
    assert not property_['error']  # Component available


def test_publish_error(Publisher, component, pubsub):
    Publisher.add_errors_listener()
    Publisher.s.add_attribute_job(component, 'wrong_property', seconds=0.1)
    Publisher.start()
    message = pubsub.get_data_message(channel='*wrong_property')
    property_ = json.loads(message['data'])
    assert property_['error']


if __name__ == '__main__':
    pytest.main()
