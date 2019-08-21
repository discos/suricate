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


def test_get_empty_jobs(client):
    """Upon start up, get an empty list of jobs"""
    response = client.get('%s/jobs' % BASE_URL)
    data = json.loads(response.data)
    assert not any(data['jobs'])


def test_create_jobs_returns_the_job(client):
    """Return the created job"""
    headers = {'content-type':'application/json'}
    response = client.post(
        '%s/jobs' %BASE_URL, data=json.dumps(DATA), headers=headers)
    assert json.loads(response.get_data()) == DATA


def test_create_and_get_jobs(client):
    """GET jobs returns the content of POST jobs."""
    headers = {'content-type':'application/json'}
    client.post('%s/jobs' %BASE_URL, data=json.dumps(DATA), headers=headers)
    response = client.get('%s/jobs' % BASE_URL)
    assert json.loads(response.get_data()) == jobs_from_data


def test_create_jobs_invalid_json(client):
    # Do not json.dumps(DATA)
    headers = {'content-type':'application/json'}
    response = client.post('%s/jobs' %BASE_URL, data=DATA, headers=headers)
    assert response.status_code == 400


if __name__ == '__main__':
    pytest.main()
