from datetime import datetime
from flask import current_app, jsonify
from . import db
from .main import main
from .tasks import command as task
from .models import Command


@main.route('/cmd/<command>', methods=['POST'])
def post_command(command):
    stime = datetime.utcnow()
    stimestr = stime.strftime("%Y-%m-%d~%H:%M:%S.%f")
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
            'error_message': "the command history list is empty"
        }
        return jsonify(response)
    else:
        return jsonify([c.serialize for c in cmds])


@main.route('/cmds/from/<stime>', methods=['GET'])
def get_commands_from_stime(stime):
    """Returns all commands from stime until now"""


@main.route('/cmds/from/<stime>/to/<etime>', methods=['GET'])
def get_commands_from_stime_to_etime(stime, etime):
    """Returns all commands from stime to etime"""
