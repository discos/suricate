from . import db


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


from flask import current_app
from sqlalchemy import create_engine
# db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
db_uri = 'sqlite://'
engine = create_engine(db_uri)
Command.metadata.create_all(engine)
