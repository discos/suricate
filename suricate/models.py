from suricate.configuration import dt_format
from suricate.api import db


class Command(db.Model):
    __tablename__ = 'commands'

    id = db.Column(db.String(128), primary_key=True)
    # The user command. I.e: 'setLO=2000,2000'
    command = db.Column(db.String(128), nullable=False)
    # Starting execution time
    stime = db.Column(db.DateTime, nullable=False)
    # Ending execution time
    etime = db.Column(db.DateTime, nullable=False)
    # Has tasks.command() been executed?  When `delivered` is
    # False, the rqworker in all likelihood was not running
    delivered = db.Column(db.Boolean, default=False)
    # Has tasks.command() terminated its execution?
    complete = db.Column(db.Boolean, default=False)
    # success is the boolean `success` returned by the Scheduler
    success = db.Column(db.Boolean, default=False)
    # result is the `answer` returned by the Scheduler
    result = db.Column(db.String(128), default='unknown')
    # How long the task has been executed?
    seconds = db.Column(db.Float, default=0.0)
    # The error message, in case the command has not been
    # delivered to the Scheduler
    error = db.Column(db.String(32), default='')

    def __repr__(self):
        return f'<Command {self.id}>'

    def get_stime(self, _dt_format=dt_format):
        return self.stime.strftime(_dt_format)

    def get_etime(self, _dt_format=dt_format):
        return self.etime.strftime(_dt_format)

    @property
    def serialize(self):
        obj_dict = dict(self.__dict__)
        del obj_dict['_sa_instance_state']
        obj_dict['stime'] = self.get_stime()
        obj_dict['etime'] = self.get_etime()
        return obj_dict


class Attribute(db.Model):
    __tablename__ = 'attributes'

    system = db.Column(db.String(128), primary_key=True)
    name = db.Column(db.String(128), primary_key=True)
    timestamp = db.Column(db.DateTime, primary_key=True)
    timer = db.Column(db.Float, nullable=False)
    value = db.Column(db.String(256))
    description = db.Column(db.String(128))
    units = db.Column(db.String(32))
    error = db.Column(db.String(128), default='')

    def __repr__(self):
        return f'<Attribute {self.system}/{self.name} @ {self.timestamp}>'

    def get_timestamp_str(self, _dt_format=dt_format):
        return self.timestamp.strftime(_dt_format)

    @property
    def serialize(self):
        obj_dict = dict(self.__dict__)
        del obj_dict['_sa_instance_state']
        obj_dict['timestamp'] = self.get_timestamp_str()
        return obj_dict


# from flask import current_app
# from sqlalchemy import create_engine
# db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
# engine = create_engine(db_uri)
# Command.metadata.create_all(engine)
# Attribute.metadata.create_all(engine)
