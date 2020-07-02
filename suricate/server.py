#! /usr/bin/env python
from __future__ import with_statement

import os
import sys
import socket
import logging
from flask import jsonify, abort, request
from flask_migrate import Migrate
from configuration import config
from monitor.core import Publisher
from api import tasks, create_app, db
from api.main import main
from api.models import Command, Attribute

publisher = None
logger = logging.getLogger('suricate')
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@main.route('/publisher/api/v0.1/jobs', methods=['GET'])
def get_jobs():
    jobs = []
    for j in publisher.s.get_jobs():
        sec, mic = j.trigger.interval.seconds, j.trigger.interval.microseconds
        jobs.append({'id': j.id, 'timer': sec + mic / (1.0 * 10 ** 6)})
    return jsonify({'jobs': jobs})


@main.route('/publisher/api/v0.1/jobs', methods=['POST'])
def create_job():
    if not request.json:
        abort(400)
    else:
        startup_delay = request.json.get('startup_delay')
        container = request.json.get('container')
        component = request.json.get('component')
        attribute = request.json.get('attribute')
        timer = request.json.get('timer')
        units = request.json.get('units', '')
        description = request.json.get('description', '')
        type_ = request.json.get('type', 'property')
        types = 'properties' if type_ == 'property' else 'methods'

    if not (component or not attribute or not timer or not container or not
            startup_delay
    ):
        logger.error('specify component, container, attribute, timer and '
                     'startup_delay')
        abort(400)
    else:
        try:
            timer = float(timer)
        except (TypeError, ValueError):
            logger.error('cannot convert %s to float' % timer)
            abort(400)

    job = {
        component: {
            "startup_delay": startup_delay,
            "container": container,
            types: [
                {
                    'name': attribute,
                    'description': description,
                    'timer': timer,
                    'units': units,
                }
            ]
        }
    }
    publisher.add_jobs(job)  # TODO: catch the exception in case of invalid job
    return jsonify({
            'component': component,
            'container': container,
            'startup_delay': startup_delay,
            'attribute': attribute,
            'description': description,
            'units': units,
            'timer': timer}
        ), 201


@main.route('/publisher/api/v0.1/config', methods=['GET'])
def get_config():
    return jsonify(config)


@main.route('/publisher/api/v0.1/stop', methods=['POST'])
def stop():  # pragma: no cover
    try:
        app_shutdown = request.environ.get('werkzeug.server.shutdown')
        if app_shutdown is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        app_shutdown()
        logger.info('the server has been stopped')
    except:
        logger.error('can not shutdown the Werkzeug server')
    finally:
        if publisher:
            publisher.shutdown()
            logger.info('all scheduled jobs have been closed')
        else:
            logger.error('there is no reference to the publisher')
    return 'Server stopped :-)'


def start_publisher(components=None):
    global publisher
    # In case a component is not available, Publisher.add_jobs()
    # writes a log an error message
    publisher = Publisher(components) if components else Publisher()
    publisher.start()


def stop_publisher():
    if publisher is not None:
        publisher.shutdown()


def start_webserver():
    try:
        app.run(debug=False)
    except socket.error, ex:
        logger.error(ex)
        sys.exit(1)


def start(components=None):
    logger.info('suricate server is starting...')
    start_publisher(components)
    start_webserver()


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Command=Command, Attribute=Attribute)
