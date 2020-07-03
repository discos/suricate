from datetime import datetime
from flask import current_app, jsonify
from suricate.api import db
from suricate.api.main import main
from suricate.api.tasks import command as task
from suricate.models import Command
from suricate.configuration import dt_format


@main.route('/cmd/<command>', methods=['POST'])
def post_command(command):
    stime = datetime.utcnow()
    stimestr = stime.strftime(dt_format)
    job_id = '{}_{}'.format(command, stimestr)
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
    )
    # The commit clears cmd.__dict__, that is
    # why I create the response before the commit.
    response = cmd.serialize
    db.session.add(cmd)
    db.session.commit()
    job = current_app.task_queue.enqueue(
        task,
        args=(command, job_id),
        job_id=job_id,
    )
    return jsonify(response)


@main.route('/cmd/<cmd_id>', methods=['GET'])
def get_command(cmd_id):
    cmd = Command.query.get(cmd_id)
    if not cmd:
        response = {
            'status_code': 404,
            'error_message': "'%s' not found in database" % cmd_id,
        }
        return jsonify(response)
    else:
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
    else:
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
    else:
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
    else:
        return jsonify([c.serialize for c in cmds])
