#! /usr/bin/env python
from __future__ import with_statement, print_function

import socket
from flask import Flask, jsonify, abort, request
from suricate.core import Publisher


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


# TODO: delete or stop one or all the jobs
# @app.route('/publisher/api/v0.1/shutdown', methods=['POST'])
# def shutdown():
#     try:
#         app_shutdown = request.environ.get('werkzeug.server.shutdown')
#         if app_shutdown is None:
#             raise RuntimeError('Not running with the Werkzeug Server')
#         app_shutdown()
#     except ?:
#         ?
#     finally:
#         publisher.shutdown()
#     return 'Server shutting down...'


def start(components=None, run_app=True):
    try:
        global publisher
        publisher = Publisher(components) if components else Publisher()
        publisher.start()
        if run_app:
            app.run(debug=True)
    except socket.error, ex:
        print(ex)


#
# if __name__ == '__main__':
#     main()
