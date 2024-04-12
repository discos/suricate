from datetime import datetime
import time
import pytest
from suricate.models import Attribute
from suricate.configuration import config, dt_format

attribute = dict(
    units='Kelvin',
    timer=0.1,
    description='A dummy attribute',
    value=100,
    error='',
)



def test_key_starts_unserscore(client, dbfiller, redis_client):
    """Do not add a key if it starts with underscore"""
    key = '__SYSTEM/Component/name'
    attribute['timestamp'] = datetime.utcnow().strftime(dt_format)
    redis_client.hset(key, mapping=attribute)
    redis_client.set('__dbfiller_stop', 'yes')
    dbfiller.dbfiller()
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result


def test_colon_in_key(client, dbfiller, redis_client):
    """Do not add the attribute if the key contains :"""
    key = 'SYSTEM/Component/name:'
    attribute['timestamp'] = datetime.utcnow().strftime(dt_format)
    redis_client.hset(key, mapping=attribute)
    redis_client.set('__dbfiller_stop', 'yes')
    dbfiller.dbfiller()
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result


def test_healthy_job_in_key(client, dbfiller, redis_client):
    """Do not add the attribute if the key contains `healthy_job`"""
    key = 'healthy_job_something'
    attribute['timestamp'] = datetime.utcnow().strftime(dt_format)
    redis_client.hset(key, mapping=attribute)
    redis_client.set('__dbfiller_stop', 'yes')
    dbfiller.dbfiller()
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result


def test_three_slash_characters_in_key(client, dbfiller, redis_client):
    """Do not add the attribute if the key does not contains exactly two /"""
    key = 'SYSTEM/Component/name/foo'
    attribute['timestamp'] = datetime.utcnow().strftime(dt_format)
    redis_client.hset(key, mapping=attribute)
    redis_client.set('__dbfiller_stop', 'yes')
    dbfiller.dbfiller()
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result


def test_do_not_store_errors(client, dbfiller, redis_client):
    """Do not add a key in case the attribute contains an error"""
    key = 'SYSTEM/Component/name'
    attribute['timestamp'] = datetime.utcnow().strftime(dt_format)
    attribute['error'] = 'an error message'
    redis_client.hset(key, mapping=attribute)
    redis_client.set('__dbfiller_stop', 'yes')
    dbfiller.dbfiller()
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result
    attribute['error'] = ''


def test_no_timestamp_in_data(client, dbfiller, redis_client):
    """The job does not brake in case there is no timestamp"""
    key = 'SYSTEM/Component/name'
    if 'timestamp' in attribute:
        del attribute['timestamp']
    redis_client.hset(key, mapping=attribute)
    redis_client.set('__dbfiller_stop', 'yes')
    dbfiller.dbfiller()
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result


def test_store_attribute(client, dbfiller, redis_client):
    """Store the attribute to db"""
    system = 'SYSTEM/Component'
    name = 'name'
    key = f'{system}/{name}'
    attribute['timestamp'] = datetime.utcnow().strftime(dt_format)
    redis_client.hset(key, mapping=attribute)
    redis_client.set('__dbfiller_stop', 'yes')
    dbfiller.dbfiller()
    result = Attribute.query.filter(
        Attribute.system == system,
        Attribute.name == name
    ).first()
    assert result.timer == attribute['timer']


def test_store_attribute_by_process(client, dbfiller, redis_client):
    """Start the process and verify it stores only one attribute"""
    system = 'SYSTEM/Component'
    name = 'name'
    key = f'{system}/{name}'
    attribute['timestamp'] = datetime.utcnow().strftime(dt_format)
    redis_client.hset(key, mapping=attribute)
    dbfiller.start()
    # Wait a little bit, to be sure the process has the
    # chance to store more than one attribute
    time.sleep(config['SCHEDULER']['dbfiller_cycle']*5)
    query = Attribute.query.filter(
        Attribute.system == system,
        Attribute.name == name
    ).all()
    # All items have different timestamp. It means in this case
    # there should be only one item stored on db
    assert len(query) == 1
    dbattr = Attribute.query.filter(
        Attribute.system == system,
        Attribute.name == name
    ).first()
    assert dbattr.timer == attribute['timer']


if __name__ == '__main__':
    pytest.main()
