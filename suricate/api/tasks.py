import logging
from datetime import datetime
from suricate.api import db
from suricate.models import Command
from suricate.errors import CannotGetComponentError

logger = logging.getLogger('suricate')


def command(line, job_id):
    import suricate.component
    try:
        cmd = Command.query.get(job_id)
        scheduler = suricate.component.Component(
            name='MANAGEMENT/Gavino',
            container='ManagementContainer',
            startup_delay=0,
        )
        cmd.success, cmd.result = scheduler.command(line)
        etime = datetime.utcnow()
        cmd.etime = etime
        cmd.seconds = (etime - cmd.stime).total_seconds()
        cmd.complete = True
    except CannotGetComponentError:
        cmd.success = False
        cmd.result = 'DISCOS Scheduler not available'
        cmd.complete = True
    except AttributeError:
        logger.error("'%s' not found in database" % job_id)
    finally:
        cmd.delivered = True
        db.session.commit()
