from datetime import datetime
from flask import current_app, jsonify
from sqlalchemy import desc
from suricate.api import db
from suricate.api.main import main
from suricate.api.tasks import command as task
from suricate.models import Command, Attribute
from suricate.configuration import dt_format


@main.route('/cmd/<command>', methods=['POST'])
def post_command(command):
    stime = datetime.utcnow()
    stimestr = stime.strftime(dt_format)
    job_id = f'{command}_{stimestr}'
    cmd = Command(
        id=job_id,
        command=command,
        stime=stime,
        etime=stime,
        delivered=False,
        complete=False,
        success=False,
        result='unknown',
        seconds=0.0,
        error='',
    )
    # The commit clears cmd.__dict__, that is
    # why I create the response before the commit.
    response = cmd.serialize
    db.session.add(cmd)
    db.session.commit()
    current_app.task_queue.enqueue(task, args=(command, job_id), job_id=job_id)
    return jsonify(response)


@main.route('/cmd/<cmd_id>', methods=['GET'])
def get_command(cmd_id):
    cmd = db.session.get(Command, cmd_id)
    if not cmd:
        response = {
            'status_code': 404,
            'error_message': f"'{cmd_id}' not found in database",
        }
        return jsonify(response)
    return jsonify(cmd.serialize)


@main.route('/cmds/<int:N>', methods=['GET'])
def get_last_commands(N):
    """Returns the last N commands"""
    query = Command.query.order_by(Command.stime.desc())
    cmds = query.limit(N).all()
    if not cmds:
        response = {
            'status_code': 404,
            'error_message': "empty command history"
        }
        return jsonify(response)
    return jsonify([c.serialize for c in cmds])


@main.route('/cmds', methods=['GET'])
def get_last_default_commands():
    """Returns the last N=10 commands"""
    return get_last_commands(10)


@main.route('/cmds/from/<dtx>', methods=['GET'])
def get_commands_from_datetimex(dtx):
    """Return all commands from datetime dtx until now"""
    try:
        dtx = datetime.strptime(dtx, dt_format)
        query = Command.query.order_by(Command.stime.desc())
        cmds = query.filter(Command.stime >= dtx).all()
    except ValueError:
        response = {
            'status_code': 400,  # Bad request
            'error_message': 'invalid datetime format',
        }
        return jsonify(response)
    if not cmds:
        response = {
            'status_code': 404,
            'error_message': "empty command history"
        }
        return jsonify(response)
    return jsonify([c.serialize for c in cmds])


@main.route('/cmds/from/<dtx>/to/<dty>', methods=['GET'])
def get_commands_from_datetimex_to_datetimey(dtx, dty):
    """Returns all commands from datetime dtx to dty"""
    try:
        dtx = datetime.strptime(dtx, dt_format)
        dty = datetime.strptime(dty, dt_format)
        query = Command.query.order_by(Command.stime.desc())
        fquery = query.filter(
            Command.stime >= dtx,
            Command.stime <= dty,
        )
        cmds = fquery.all()
    except ValueError:
        response = {
            'status_code': 400,  # Bad request
            'error_message': 'invalid datetime format',
        }
        return jsonify(response)
    if not cmds:
        response = {
            'status_code': 404,
            'error_message': "empty command history"
        }
        return jsonify(response)
    return jsonify([c.serialize for c in cmds])


@main.route('/attr/<system>/<component>/<name>/<int:N>', methods=['GET'])
def get_last_attribute_values(system, component, name, N):
    """Returns the last N commands"""
    key = f'{system}/{component}/{name}'
    attrs = Attribute.query.filter(Attribute.name == key)
    attrs = attrs.order_by(desc(Attribute.timestamp)).limit(N).all()
    if not attrs:
        response = {
            'status_code': 404,
            'error_message': "empty attribute history"
        }
        return jsonify(response)
    return jsonify([a.serialize for a in attrs])


@main.route('/attr/<system>/<component>/<name>', methods=['GET'])
def get_last_default_attribute_values(system, component, name):
    """Returns the last N=10 values"""
    return get_last_attribute_values(system, component, name, 10)


@main.route('/attr/<system>/<component>/<name>/from/<dtx>', methods=['GET'])
def get_attribute_from_datetimex(system, component, name, dtx):
    """Return all attributes values from datetime dtx until now"""
    key = f'{system}/{component}/{name}'
    try:
        dtx = datetime.strptime(dtx, dt_format)
        attrs = Attribute.query.filter(
            Attribute.name == key,
            Attribute.timestamp >= dtx,
        ).order_by(Attribute.timestamp.desc()).all()
    except ValueError:
        response = {
            'status_code': 400,  # Bad request
            'error_message': 'invalid datetime format',
        }
        return jsonify(response)
    if not attrs:
        response = {
            'status_code': 404,
            'error_message': "empty attribute history"
        }
        return jsonify(response)
    return jsonify([a.serialize for a in attrs])


@main.route(
    '/attr/<system>/<component>/<name>/from/<dtx>/to/<dty>',
    methods=['GET']
)
def get_attribute_from_datetimex_to_datetimey(
    system,
    component,
    name,
    dtx,
    dty
):
    """Returns all attribute values from datetime dtx to dty"""
    key = f'{system}/{component}/{name}'
    try:
        dtx = datetime.strptime(dtx, dt_format)
        dty = datetime.strptime(dty, dt_format)
        attrs = Attribute.query.filter(
            Attribute.name == key,
            Attribute.timestamp >= dtx,
            Attribute.timestamp <= dty,
        ).order_by(Attribute.timestamp.desc()).all()
    except ValueError:
        response = {
            'status_code': 400,  # Bad request
            'error_message': 'invalid datetime format',
        }
        return jsonify(response)
    if not attrs:
        response = {
            'status_code': 404,
            'error_message': "empty attribute history"
        }
        return jsonify(response)
    return jsonify([a.serialize for a in attrs])
