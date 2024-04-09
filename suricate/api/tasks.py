import logging
from datetime import datetime
from suricate.api import db
from suricate.models import Command
from suricate.errors import CannotGetComponentError

logger = logging.getLogger('suricate')


def command(line, cmd_id):
    import suricate.component
    import suricate.services
    container = 'ManagementContainer'
    try:
        cmd = db.session.get(Command, cmd_id)
        if not suricate.services.is_manager_online():
            cmd.success = False
            cmd.complete = False
            cmd.error = 'ACS not running'
        elif not suricate.services.is_container_online(container):
            cmd.success = False
            cmd.complete = False
            cmd.error = '%s not running' % container
        else:
            scheduler = suricate.component.Component(
                name='MANAGEMENT/Gavino',
                container=container,
                startup_delay=0,
            )
            cmd.success, cmd.result = scheduler.command(line)
            etime = datetime.utcnow()
            cmd.etime = etime
            cmd.seconds = (etime - cmd.stime).total_seconds()
            cmd.complete = True
    except CannotGetComponentError:
        cmd.success = False
        cmd.complete = True
        cmd.error = 'DISCOS Scheduler not available'
    except AttributeError:
        logger.error("'%s' not found in database" % cmd_id)
    finally:
        if cmd:
            cmd.delivered = True
            db.session.add(cmd)
            db.session.commit()
