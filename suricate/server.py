#! /usr/bin/env python
import sys
import socket
import logging
from flask import jsonify, abort, request
from flask_migrate import Migrate
from suricate.configuration import config
from suricate.monitor.core import Publisher
from suricate.api import create_app, db
from suricate.api.main import main
from suricate.models import Command, Attribute
from suricate.dbfiller import DBFiller
logging._srcfile = None


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

    if None in [component, container, attribute, timer, startup_delay]:
        logger.error(
            'specify component, container, attribute, timer and startup_delay'
        )
        abort(400)
    else:
        try:
            timer = float(timer)
        except (TypeError, ValueError):
            logger.error('cannot convert %s to float', timer)
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
    return jsonify(
        {
            'component': component,
            'container': container,
            'startup_delay': startup_delay,
            'attribute': attribute,
            'description': description,
            'units': units,
            'timer': timer
        }
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
        if dbfiller:
            dbfiller.shutdown()
            logger.info('dbfiller job has been closed')
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


def start_dbfiller():
    dbfiller.start()


def stop_dbfiller():
    if dbfiller is not None:
        dbfiller.shutdown()


def start_webserver():
    try:
        app.run(debug=False)
    except socket.error as ex:
        logger.error(ex)
        sys.exit(1)


def start(components=None):
    logger.info('suricate server is starting...')
    start_publisher(components)
    start_dbfiller()
    start_webserver()


publisher = None
dbfiller = DBFiller()
logger = logging.getLogger('suricate')
app = create_app(config['DATABASE'])
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Command': Command, 'Attribute': Attribute}
