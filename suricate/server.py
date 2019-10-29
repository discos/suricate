#! /usr/bin/env python
from __future__ import with_statement, print_function

import time
import sys
import socket
from flask import Flask, jsonify, abort, request
from suricate.core import Publisher
from suricate.errors import CannotGetComponentError


app = Flask(__name__)
publisher = None


@app.route('/publisher/api/v0.1/jobs', methods=['GET'])
def get_jobs():
    jobs = []
    for j in publisher.s.get_jobs():
        sec, mic = j.trigger.interval.seconds, j.trigger.interval.microseconds
        jobs.append({'id': j.id, 'timer': sec + mic / (1.0 * 10 ** 6)})
    return jsonify({'jobs': jobs})


@app.route('/publisher/api/v0.1/jobs', methods=['POST'])
def create_job():
    if not request.json:
        abort(400)
    else:
        component = request.json.get('component')
        attribute = request.json.get('attribute')
        timer = request.json.get('timer')
        description = request.json.get('description', '')

    if not component or not attribute or not timer:
        abort(400)
    else:
        try:
            timer = float(timer)
        except (TypeError, ValueError):
            abort(400)

    job = {
        component: [
            {'name': attribute, 'description': description, 'timer': timer}
        ]
    }
    publisher.add_jobs(job)  # TODO: catch the exception in case of invalid job
    return jsonify({
        'component': component,
        'attribute': attribute,
        'timer': timer}), 201


@app.route('/publisher/api/v0.1/stop', methods=['POST'])
def stop():  # pragma: no cover
    msg = '\n'
    try:
        app_shutdown = request.environ.get('werkzeug.server.shutdown')
        if app_shutdown is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        app_shutdown()
        msg += 'The server has been stopped\n'
    except:
        msg += 'Can not shutdown the Werkzeug server\n'
    finally:
        if publisher:
            publisher.shutdown()
            msg += 'All scheduled jobs have been closed\n'
        else:
            msg += 'ERROR: there is no reference to the publisher\n'
        time.sleep(5)
        print(msg)
    return 'Server stopped :-)'


def start_publisher(components=None):
    try:
        global publisher
        publisher = Publisher(components) if components else Publisher()
        publisher.start()
    except CannotGetComponentError, ex:
        print('\nERROR: %s.' % ex)
        print('Is the component listed in the configuration file?\n')
        sys.exit(1)


def stop_publisher():
    if publisher is not None:
        publisher.shutdown()


def start_webserver():
    try:
        app.run(debug=False)
    except socket.error, ex:
        print(ex)
        sys.exit(1)


def start(components=None):
    start_publisher(components)
    start_webserver()
