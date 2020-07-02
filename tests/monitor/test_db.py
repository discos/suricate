from datetime import datetime
import time
import pytest
from suricate.api.models import Attribute
from suricate.configuration import config, dt_format

attribute = dict(
    units='Kelvin',
    timer=0.1,
    description='A dummy attribute',
    value=100,
    error='',
)


def test_add_attribute(client, Publisher, redis_client):
    """The attribute is stored on db"""
    p = Publisher(config['COMPONENTS'])
    p.start()
    key = 'SYSTEM/Component/name'
    t = datetime.utcnow()
    attribute['timestamp'] = t.strftime(dt_format)
    redis_client.hmset(key, attribute)
    time.sleep(config['SCHEDULER']['db_scheduler_job']*3)
    query = Attribute.query.filter(Attribute.name == key).all()
    # All items have different timestamp. It means in this case
    # there should be only one item stored on db
    assert len(query) == 1
    dbattr = Attribute.query.filter(Attribute.name == key).first()
    assert dbattr.timer == attribute['timer']


def test_key_starts_unserscore(client, Publisher, redis_client):
    """Do not add a key if it starts with underscore"""
    p = Publisher(config['COMPONENTS'])
    p.start()
    key = '__SYSTEM/Component/name'
    t = datetime.utcnow()
    attribute['timestamp'] = t.strftime(dt_format)
    redis_client.hmset(key, attribute)
    time.sleep(config['SCHEDULER']['db_scheduler_job']*3)
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result


def test_colon_in_key(client, Publisher, redis_client):
    """Do not add the attribute if the key contains :"""
    p = Publisher(config['COMPONENTS'])
    p.start()
    key = 'SYSTEM/Compnent/name:'
    t = datetime.utcnow()
    attribute['timestamp'] = t.strftime(dt_format)
    redis_client.hmset(key, attribute)
    time.sleep(config['SCHEDULER']['db_scheduler_job']*3)
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result


def test_three_slash_characters_in_key(client, Publisher, redis_client):
    """Do not add the attribute if the key does not contains exactly two /"""
    p = Publisher(config['COMPONENTS'])
    p.start()
    key = 'SYSTEM/Component/name/foo'
    t = datetime.utcnow()
    attribute['timestamp'] = t.strftime(dt_format)
    redis_client.hmset(key, attribute)
    time.sleep(config['SCHEDULER']['db_scheduler_job']*3)
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result


def test_do_not_store_errors(client, Publisher, redis_client):
    """Do not add a key in case the attribute contains an error"""
    p = Publisher(config['COMPONENTS'])
    p.start()
    key = 'SYSTEM/Component/name'
    t = datetime.utcnow()
    attribute['timestamp'] = t.strftime(dt_format)
    attribute['error'] = 'an error message'
    redis_client.hmset(key, attribute)
    time.sleep(config['SCHEDULER']['db_scheduler_job']*3)
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result


def test_no_timestamp_in_data(client, Publisher, redis_client):
    """The job does not brake in case there is no timestamp"""
    p = Publisher(config['COMPONENTS'])
    p.start()
    key = 'SYSTEM/Component/name'
    t = datetime.utcnow()
    # Notice: I am not adding the timestamp field
    redis_client.hmset(key, attribute)
    time.sleep(config['SCHEDULER']['db_scheduler_job']*3)
    result = Attribute.query.filter(Attribute.name == key).all()
    assert not result



if __name__ == '__main__':
    pytest.main()
