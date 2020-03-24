import time
import json
import pytest

from suricate.configuration import config


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


def test_set_publish_property_value(component, scheduler, pubsub, redis_client):
    """Verify the job gets and publishes/sets the property value"""
    value = 3
    component.setPosition(value)
    job = scheduler.add_attribute_job(component, 'position', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*position')
    prop = json.loads(message['data'])
    assert not prop['error']
    assert float(prop['value']) == float(value)
    component.setPosition(value)
    time.sleep(0.1)
    job_id = '%s/position' % component.name
    assert float(redis_client.hget(job_id, 'value')) == float(value)


def test_unit_and_description(Publisher, pubsub):
    """Positioner00/position has units and description set in configuration.py"""
    p = Publisher(config['COMPONENTS'])
    p.start()
    time.sleep(config['SCHEDULER']['reschedule_error_interval']*1.2)
    message = pubsub.get_data_message(channel='*position')
    prop = json.loads(message['data'])
    assert prop['description'] == 'current position'
    assert prop['units'] == 'mm'


def test_default_unit_and_description(Publisher, pubsub):
    """Positioner00/current has no units and description set in configuration.py"""
    p = Publisher(config['COMPONENTS'])
    p.start()
    time.sleep(config['SCHEDULER']['reschedule_error_interval']*1.2)
    message = pubsub.get_data_message(channel='*current')
    prop = json.loads(message['data'])
    assert prop['description'] == ''
    assert prop['units'] == ''


def test_set_publish_property_sequence_value(component, scheduler, pubsub, redis_client):
    """Verify the job gets and publishes/sets the sequence property value"""
    seq1 = (1.1, 2.2, 3.3, 4.4)
    component.setSequence(seq1)
    job = scheduler.add_attribute_job(component, 'seq', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*seq')
    prop = json.loads(message['data'])
    assert not prop['error']
    assert prop['value'] == str(seq1)
    seq2 = (11.1, 12.2, 13.3, 14.4)
    component.setSequence(seq2)
    time.sleep(0.1)
    job_id = '%s/seq' % component.name
    assert redis_client.hget(job_id, 'value') == str(seq2)


def test_set_publish_method_value(component, scheduler, pubsub, redis_client):
    """Verify the job gets and publishes/sets the method value"""
    value = 3
    component.setPosition(value)
    job = scheduler.add_attribute_job(component, 'getPosition', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*getPosition')
    prop = json.loads(message['data'])
    assert float(prop['value']) == float(value)
    assert not prop['error']
    component.setPosition(value)
    time.sleep(0.1)
    job_id = '%s/getPosition' % component.name
    assert float(redis_client.hget(job_id, 'value')) == float(value)


def test_set_publish_method_sequence_value(component, scheduler, pubsub, redis_client):
    """Verify the job gets and publishes/sets the sequence method value"""
    seq1 = (1.1, 2.2, 3.3, 4.4)
    component.setSequence(seq1)
    job = scheduler.add_attribute_job(component, 'getSequence', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*getSequence')
    prop = json.loads(message['data'])
    assert prop['value'] == str(seq1)
    assert not prop['error']
    seq2 = (11.1, 12.2, 13.3, 14.4)
    component.setSequence(seq2)
    time.sleep(0.1)
    job_id = '%s/getSequence' % component.name
    assert redis_client.hget(job_id, 'value') == str(seq2)


def test_wrong_property_name(component, scheduler, pubsub):
    job = scheduler.add_attribute_job(component, 'wrong', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*wrong')
    prop = json.loads(message['data'])
    assert prop['error'] != ''
    assert prop['value'] == ''


def test_broken_reference(component, scheduler, pubsub):
    component.release()
    job = scheduler.add_attribute_job(component, 'position', seconds=0.01)
    scheduler.wait_until_executed(job)
    message = pubsub.get_data_message(channel='*position')
    prop = json.loads(message['data'])
    assert prop['error']
    assert prop['value'] == ''


def test_attribute_proxy(component):
    """The Proxy gets the Python attributes of its object"""
    attribute = component._get_position
    assert attribute.__name__ == '_get_position'


def test_set_property_value(component, scheduler, pubsub):
    """Verify the job gets and publishes the property value"""
    value = 3.0
    component.setPosition(value)  # Set the position property to 3
    job = scheduler.add_attribute_job(component, 'position', seconds=0.01)
    scheduler.wait_until_executed(job)
    pubsub.get_data_message(channel='*position')  # Wait the data to be ready
    msg = pubsub._redis.hgetall(job.id)  # The value is currently set
    assert float(msg['value']) == value
    assert msg['error'] == ''
    assert msg['timestamp']


if __name__ == '__main__':
    pytest.main()
