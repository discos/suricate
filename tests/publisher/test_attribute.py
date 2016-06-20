import pytest
import json


def test_publish_to_default_channel(component, scheduler, pubsub):
    """Publishing to the default channel `namespace/component/attribute"""
    job = scheduler.add_attribute_job(component, 'position', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*position')
    # We expect to get a message from the default channel
    default_name = '/'.join([component.name, 'position'])
    assert message['channel'] == default_name


def test_publish_to_custom_channel(component, scheduler, pubsub):
    """Publishing to a custom channel"""
    job = scheduler.add_attribute_job(
        component, 'position', seconds=0.01, channel='my-channel')
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='my-*')
    assert message['channel'] == 'my-channel'


def test_publish_attribute_value(component, scheduler, pubsub):
    """Verify the job gets and publishes the attribute value"""
    component.setPosition(3)  # Set the position attribute to 3
    job = scheduler.add_attribute_job(component, 'position', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*position')
    attribute = json.loads(message['data'])
    assert attribute['value'] == 3
    assert not attribute['error']


def test_wrong_attribute_name(component, scheduler, pubsub):
    job = scheduler.add_attribute_job(component, 'wrong', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*wrong')
    attribute = json.loads(message['data'])
    assert attribute['error']
    assert attribute['value'] is None


def test_broken_reference(component, scheduler, pubsub):
    component.release()
    job = scheduler.add_attribute_job(component, 'position', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*position')
    attribute = json.loads(message['data'])
    assert attribute['error']
    assert attribute['value'] is None


def test_attribute_proxy(component):
    """The Proxy gets the Python attributes of its object"""
    attribute = component._get_position
    assert attribute.__name__ == '_get_position'


def test_set_attribute_value(component, scheduler, pubsub):
    """Verify the job gets and publishes the attribute value"""
    value = 3.0
    component.setPosition(value)  # Set the position attribute to 3
    job = scheduler.add_attribute_job(component, 'position', seconds=0.01)
    scheduler.wait_until_executed(job)
    pubsub.get_data_message(channel='*position')  # Wait the data to be ready
    msg = pubsub._redis.get(job.id)  # The value is currently set
    v, _ = msg.split('@')  # Value, timestamp
    assert float(v) == value


if __name__ == '__main__':
    pytest.main()
