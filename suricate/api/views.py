from datetime import datetime
from flask import current_app
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
    response = dict(cmd.__dict__)
    del response['_sa_instance_state']
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
        response = cmd.__dict__
        del response['_sa_instance_state']
        return jsonify(response)
