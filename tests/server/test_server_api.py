from flask import json

import pytest


BASE_URL = '/publisher/api/v0.1'

DATA = {
    'component': 'TestNamespace/Positioner',
    'attribute': 'position',
    'timer': 0.1
}


jobs_from_data = {
    'jobs':
        [
            {
                'id': '%s/%s' % (DATA['component'], DATA['attribute']),
                'timer': DATA['timer']
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
        '%s/jobs' %BASE_URL, data=json.dumps(DATA), headers=HEADERS)
    assert json.loads(response.get_data()) == DATA


def test_create_and_get_jobs(client):
    """GET jobs returns the content of POST jobs."""
    client.post('%s/jobs' %BASE_URL, data=json.dumps(DATA), headers=HEADERS)
    response = client.get('%s/jobs' % BASE_URL)
    assert json.loads(response.get_data()) == jobs_from_data


def test_create_jobs_invalid_json(client):
    # Do not json.dumps(DATA)
    response = client.post('%s/jobs' %BASE_URL, data=DATA, headers=HEADERS)
    assert response.status_code == 400


def test_create_jobs_empty_json(client):
    response = client.post('%s/jobs' %BASE_URL, data={})
    assert response.status_code == 400


def test_stop(client, monkeypatch):
    monkeypatch.setattr('suricate.server.publisher.shutdown', lambda: None)
    response = client.post('%s/stop' %BASE_URL)
    assert response.get_data() == 'Server stopped :-)'


if __name__ == '__main__':
    pytest.main()
