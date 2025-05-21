import time
from datetime import datetime
from flask import json, jsonify
import pytest
import suricate
from suricate.configuration import dt_format
from suricate.configuration import default_config as config


BASE_URL = '/publisher/api/v0.1'

DATA = dict(
    component='TestNamespace/Positioner',
    startup_delay=0,
    container='PositionerContainer',
    attribute='position',
    description='a brief description',
    units='mm',
    timer=0.1,
    type='property',
)


ATTRIBUTE = dict(
    units='Kelvin',
    timer=0.1,
    timestamp=datetime.utcnow().strftime(dt_format),
    description='A dummy attribute',
    value='100',
    error='',
)



jobs_from_data = {
    'jobs':
        [
            {
                'id': '%s/%s' % (DATA['component'], DATA['attribute']),
                'timer': DATA['timer'],
            }
        ]
}


HEADERS = {'content-type':'application/json'}


def test_get_empty_jobs(client):
    """Upon start up, get an empty list of jobs"""
    response = client.get('%s/jobs' % BASE_URL)
    data = json.loads(response.data)
    assert not any(data['jobs'])


def test_create_jobs_returns_the_job(client):
    """Return the created job"""
    response = client.post(
        '%s/jobs' % BASE_URL, data=json.dumps(DATA), headers=HEADERS)
    answer = DATA.copy()
    del answer['type']
    assert response.get_json() == answer


def test_create_and_get_jobs(client):
    """GET jobs returns the content of POST jobs."""
    client.post('%s/jobs' % BASE_URL, data=json.dumps(DATA), headers=HEADERS)
    response = client.get('%s/jobs' % BASE_URL)
    assert response.get_json() == jobs_from_data


def test_create_jobs_invalid_json(client):
    # Do not json.dumps(DATA)
    response = client.post('%s/jobs' % BASE_URL, data=DATA, headers=HEADERS)
    assert response.status_code == 400


def test_create_jobs_empty_json(client):
    response = client.post(
        '%s/jobs' % BASE_URL,
        data={},
        headers=HEADERS
    )
    assert response.status_code == 400


def test_stop(client, monkeypatch):
    monkeypatch.setattr('suricate.server.publisher.shutdown', lambda: None)
    response = client.post('%s/stop' % BASE_URL)
    assert response.get_data() == b'Server stopped :-)'


def test_get_configuration(client):
    """Get the running configuration"""
    response = client.get('%s/config' % BASE_URL)
    from suricate.configuration import config
    response_config = response.get_json()
    assert response_config == config


def test_post_command(client):
    """Call the server.post_command() method"""
    cmd = 'getTpi'
    raw_response = client.post('/cmd/%s' % cmd)
    response = raw_response.get_json()
    job_id = response['id']
    assert '_' in job_id
    assert cmd == job_id.split('_')[0]
    assert response['command'] == cmd
    assert response['stime'] == response['etime']
    assert not response['delivered']
    assert not response['complete']
    assert not response['success']
    assert response['result'] == 'unknown'
    assert response['seconds'] == 0.0


def test_execute_command(client):
    """Call the api.tasks.command() method"""
    cmd = 'getTpi'
    raw_response = client.post('/cmd/%s' % cmd)
    post_response = raw_response.get_json()
    job_id = post_response['id']
    # time.sleep(0.5)
    raw_response = client.get('/cmd/%s' % job_id)
    get_response = raw_response.get_json()
    assert get_response['command'] == cmd
    assert get_response['complete']
    assert get_response['delivered']
    assert get_response['stime'] <= get_response['etime']
    assert get_response['success']
    assert 'getTpi\\\n00)' in get_response['result']
    assert get_response['seconds'] > 0.0


def test_not_success(client):
    """Scheduler.command() unsuccessful."""
    cmd = 'wrongCommand'
    raw_response = client.post('/cmd/%s' % cmd)
    post_response = raw_response.get_json()
    job_id = post_response['id']
    # time.sleep(0.5)
    raw_response = client.get('/cmd/%s' % job_id)
    get_response = raw_response.get_json()
    assert get_response['command'] == cmd
    assert get_response['complete']
    assert get_response['delivered']
    assert get_response['stime'] <= get_response['etime']
    assert not get_response['success']
    assert 'wrongCommand?' in get_response['result']
    assert get_response['seconds'] > 0.0


def test_get_last_commands(client):
    """Get the last N executed commands.
    This test checks also the case of GET /cmds/N"""
    client.post('/cmd/moo')
    time.sleep(0.01)
    client.post('/cmd/foo')
    time.sleep(0.01)
    client.post('/cmd/getTpi')
    time.sleep(0.01)
    raw_response = client.get('/cmds/10')
    response = raw_response.get_json()
    assert len(response) == 3
    assert response[2]['command'] == 'moo'
    raw_response = client.get('/cmds/2')
    response = raw_response.get_json()
    assert len(response) == 2
    assert response[0]['command'] == 'getTpi'


def test_get_last_default_commands(client):
    """Without N, GET /cmds returns the last 10 commands"""
    for i in range(15):
        client.post('/cmd/foo')
    time.sleep(0.01)
    raw_response = client.get('/cmds')
    response = raw_response.get_json()
    assert len(response) == 10


def test_empty_commands_history(client):
    raw_response = client.get('/cmds')
    response = raw_response.get_json()
    assert response['status_code'] == 404
    assert response['error_message'] == 'empty command history'


def test_get_commands_from_datetimex(client):
    """Get all commands from datetime dtx until now"""
    client.post('/cmd/command_1')
    time.sleep(0.01)
    raw_response = client.post('/cmd/command_2')
    post_response = raw_response.get_json()
    dtx = post_response['stime']
    client.post('/cmd/command_3')
    client.post('/cmd/command_4')
    time.sleep(0.1)
    raw_response = client.get('/cmds')
    response = raw_response.get_json()
    assert len(response) == 4
    raw_response = client.get('/cmds/from/%s' % dtx)
    response = raw_response.get_json()
    assert len(response) == 3


def test_get_commands_from_invalid_datetimex(client):
    """Test invalid datetime format in GET /cmds/from/dtx"""
    raw_response = client.get('/cmds/from/wrong_dtx')
    response = raw_response.get_json()
    assert response['status_code'] == 400
    assert response['error_message'] == 'invalid datetime format'


def test_empty_commands_history_from_datetimex(client):
    dtx = datetime.utcnow().strftime(dt_format)
    raw_response = client.get('/cmds/from/%s' % dtx)
    response = raw_response.get_json()
    assert response['status_code'] == 404
    assert response['error_message'] == 'empty command history'


def test_get_commands_from_datetimex_to_datetimey(client):
    """Get all commands from datetime dtx to dty"""
    client.post('/cmd/command_1')
    time.sleep(0.01)
    raw_response = client.post('/cmd/command_2')
    post_response = raw_response.get_json()
    dtx = post_response['stime']
    raw_response = client.post('/cmd/command_3')
    post_response = raw_response.get_json()
    dty = post_response['stime']
    client.post('/cmd/command_4')  # cmd n.4
    time.sleep(0.1)
    raw_response = client.get('/cmds')
    response = raw_response.get_json()
    assert len(response) == 4
    raw_response = client.get('/cmds/from/%s/to/%s' % (dtx, dty))
    response = raw_response.get_json()
    assert len(response) == 2


def test_get_commands_from_invalid_datetimex_to_datetimey(client):
    """Test invalid datetime format in GET /cmds/from/dtx/to/dty"""
    raw_response = client.get('/cmds/from/wrong_dtx/to/wrong_dty')
    response = raw_response.get_json()
    assert response['status_code'] == 400
    assert response['error_message'] == 'invalid datetime format'


def test_empty_commands_history_from_datetimex_to_datetimey(client):
    dtx = datetime.utcnow().strftime(dt_format)
    dty = datetime.utcnow().strftime(dt_format)
    raw_response = client.get('/cmds/from/%s/to/%s' % (dtx, dty))
    response = raw_response.get_json()
    assert response['status_code'] == 404
    assert response['error_message'] == 'empty command history'


def test_scheduler_not_available(client):
    """The component is not available."""
    try:
        suricate.component.Component.unavailables = ['MANAGEMENT/Gavino']
        raw_response = client.post('/cmd/foo')
        response = raw_response.get_json()
        cmd_id = response['id']
        raw_response = client.get('/cmd/%s' % cmd_id)
        time.sleep(0.01)
        response = raw_response.get_json()
        assert response['delivered'] == True
        assert response['complete'] == True
        assert response['success'] == False
        assert response['result'] == 'unknown'
        assert response['error'] == 'DISCOS Scheduler not available'
    finally:
        suricate.component.Component.unavailables = []


def test_manager_offline(client):
    try:
        suricate.services.is_manager_online = lambda: False
        raw_response = client.post('/cmd/foo')
        response = raw_response.get_json()
        cmd_id = response['id']
        raw_response = client.get('/cmd/%s' % cmd_id)
        time.sleep(0.01)
        response = raw_response.get_json()
        assert response['delivered'] == True
        assert response['complete'] == False
        assert response['success'] == False
        assert response['result'] == 'unknown'
        assert response['error'] == 'ACS not running'
    finally:
        suricate.services.is_manager_online = lambda: True


def test_container_offline(client):
    try:
        suricate.services.is_manager_online = lambda: True
        suricate.services.is_container_online = lambda x: False
        raw_response = client.post('/cmd/foo')
        response = raw_response.get_json()
        cmd_id = response['id']
        raw_response = client.get('/cmd/%s' % cmd_id)
        time.sleep(0.01)
        response = raw_response.get_json()
        assert response['delivered'] == True
        assert response['complete'] == False
        assert response['success'] == False
        assert response['result'] == 'unknown'
        assert response['error'] == 'ManagementContainer not running'
    finally:
        suricate.services.is_container_online = lambda x: True


def test_get_last_attributes(client, dbfiller, redis_client):
    """Get the last N values of Positioner00/current."""
    key1 = 'SYSTEM/Component/name1'
    key2 = 'SYSTEM/Component/name2'
    N = 5
    dbfiller.start()
    for i in range(N):
        ATTRIBUTE['timestamp'] = datetime.utcnow().strftime(dt_format)
        redis_client.hset(key1, mapping=ATTRIBUTE)
        redis_client.hset(key2, mapping=ATTRIBUTE)
        time.sleep(config['SCHEDULER']['dbfiller_cycle']*2)
    raw_response = client.get('/attr/%s/%d' % (key1, N))
    response = raw_response.get_json()
    assert len(response) == N
    assert response[0]['system'] == 'SYSTEM/Component'
    assert response[0]['name'] == 'name1'
    assert response[0]['value'] == ATTRIBUTE['value']
    assert response[0]['timestamp'] > response[N-1]['timestamp']
    raw_response = client.get('/attr/%s/%d' % (key2, N-1))
    response = raw_response.get_json()
    assert len(response) == (N - 1)


def test_get_last_default_attribute(client, dbfiller, redis_client):
    """Without N, GET /attr returns the last 10 values"""
    key = 'SYSTEM/Component/name'
    dbfiller.start()
    for i in range(15):
        ATTRIBUTE['timestamp'] = datetime.utcnow().strftime(dt_format)
        redis_client.hset(key, mapping=ATTRIBUTE)
        time.sleep(config['SCHEDULER']['dbfiller_cycle']*2)
    raw_response = client.get('/attr/%s' % key)
    response = raw_response.get_json()
    assert len(response) == 10


def test_empty_attribute_history(client):
    raw_response = client.get('/attr/sys/comp/namefoo')
    response = raw_response.get_json()
    assert response['status_code'] == 404
    assert response['error_message'] == 'empty attribute history'


def test_get_attribute_from_datetimex(client, dbfiller, redis_client):
    """Get all attribute values from datetime dtx until now"""
    key = 'SYSTEM/Component/name'
    M = 2
    N = 3
    dbfiller.start()

    # Add M attribute values before datetime dtx
    for i in range(M):
        ATTRIBUTE['timestamp'] = datetime.utcnow().strftime(dt_format)
        redis_client.hset(key, mapping=ATTRIBUTE)
        time.sleep(config['SCHEDULER']['dbfiller_cycle']*2)

    # Add N attribute values after datetime dtx
    dtx = datetime.utcnow().strftime(dt_format)
    for i in range(N):
        ATTRIBUTE['timestamp'] = datetime.utcnow().strftime(dt_format)
        redis_client.hset(key, mapping=ATTRIBUTE)
        time.sleep(config['SCHEDULER']['dbfiller_cycle']*2)

    raw_response = client.get('/attr/%s' % key)
    response = raw_response.get_json()
    assert len(response) == (M + N)
    raw_response = client.get('/attr/%s/from/%s' % (key, dtx))
    response = raw_response.get_json()
    assert len(response) == N
    assert response[0]['timestamp'] > response[N-1]['timestamp']


def test_get_attributes_from_invalid_datetimex(client):
    """Test invalid datetime format in GET /attr/.../from/dtx"""
    key = 'SYSTEM/Component/name'
    raw_response = client.get('/attr/%s/from/wrong_dtx' % key)
    response = raw_response.get_json()
    assert response['status_code'] == 400
    assert response['error_message'] == 'invalid datetime format'


def test_empty_attribute_history_from_datetimex(client):
    key = 'sys/comp/namefoo'
    dtx = datetime.utcnow().strftime(dt_format)
    raw_response = client.get('/attr/%s/from/%s' % (key, dtx))
    response = raw_response.get_json()
    assert response['status_code'] == 404
    assert response['error_message'] == 'empty attribute history'


def test_get_attribute_from_datetimex_to_datetimey(client, dbfiller, redis_client):
    """Get all attributes from datetime dtx to dty"""
    key = 'SYSTEM/Component/name'
    M = 2
    N = 3
    K = 2
    dbfiller.start()

    # Add M attribute values before datetime dtx
    for i in range(M):
        ATTRIBUTE['timestamp'] = datetime.utcnow().strftime(dt_format)
        redis_client.hset(key, mapping=ATTRIBUTE)
        time.sleep(config['SCHEDULER']['dbfiller_cycle']*2)

    # Add N attribute values after datetime dtx
    dtx = datetime.utcnow().strftime(dt_format)
    for i in range(N):
        ATTRIBUTE['timestamp'] = datetime.utcnow().strftime(dt_format)
        redis_client.hset(key, mapping=ATTRIBUTE)
        time.sleep(config['SCHEDULER']['dbfiller_cycle']*2)

    # Add K attribute values after datetime dty
    dty = datetime.utcnow().strftime(dt_format)
    for i in range(K):
        ATTRIBUTE['timestamp'] = datetime.utcnow().strftime(dt_format)
        redis_client.hset(key, mapping=ATTRIBUTE)
        time.sleep(config['SCHEDULER']['dbfiller_cycle']*2)

    raw_response = client.get('/attr/%s' % key)
    response = raw_response.get_json()
    assert len(response) == (M + N + K)
    raw_response = client.get('/attr/%s/from/%s/to/%s' % (key, dtx, dty))
    response = raw_response.get_json()
    assert len(response) == N
    assert response[0]['timestamp'] > response[N-1]['timestamp']


def test_get_attribute_from_invalid_datetimex_to_datetimey(client):
    """Test invalid datetime format in GET /attr/.../from/dtx/to/dty"""
    key = 'SYSTEM/Component/name'
    raw_response = client.get('/attr/%s/from/wrong_dtx/to/wrong_dty' % key)
    response = raw_response.get_json()
    assert response['status_code'] == 400
    assert response['error_message'] == 'invalid datetime format'


def test_empty_attribute_history_from_datetimex_to_datetimey(client):
    key = 'sys/comp/namefoo'
    dtx = datetime.utcnow().strftime(dt_format)
    dty = datetime.utcnow().strftime(dt_format)
    raw_response = client.get('/attr/%s/from/%s/to/%s' % (key, dtx, dty))
    response = raw_response.get_json()
    assert response['status_code'] == 404
    assert response['error_message'] == 'empty attribute history'


if __name__ == '__main__':
    pytest.main()
