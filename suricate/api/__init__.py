from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from rq import Queue
from .config import api_config

db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(api_config[config_name])
    api_config[config_name].init_app(app)
    db.init_app(app)
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = Queue(
        'discos-api',
        is_async=app.config['IS_ASYNC_QUEUE'],
        connection=app.redis
    )
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return app

