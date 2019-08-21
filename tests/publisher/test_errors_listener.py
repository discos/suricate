"""Errors notified to the listener"""
import json

import pytest


def test_reload_component(Publisher, Component, pubsub):
    """Docstring"""
    Publisher.add_errors_listener()
    component = Component('TestNamespace/Positioner')
    Publisher.s.add_attribute_job(component, 'position', seconds=0.1)
    component.release()
    Publisher.start()
    message = pubsub.get_data_message(channel='*position')
    property_ = json.loads(message['data'])
    assert property_['error']  # Component not available
    message = pubsub.get_data_message(channel='*position')
    property_ = json.loads(message['data'])
    assert not property_['error']  # Component available


def test_cannot_reload_component(Publisher, Component, pubsub):
    Publisher.add_errors_listener()
    component = Component('TestNamespace/Positioner')
    component.name = 'foo'
    Publisher.s.add_attribute_job(component, 'wrong_property', seconds=0.1)
    Publisher.start()
    for _ in range(2):
        message = pubsub.get_data_message(channel='*wrong_property')
        property_ = json.loads(message['data'])
        assert property_['error']


if __name__ == '__main__':
    pytest.main()
