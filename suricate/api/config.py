import os
from suricate.paths import database_dir


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'HardToGuessString'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = \
        os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SURICATE_ADMIN = os.environ.get('SURICATE_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = 'redis://'
    TESTING = False
    IS_ASYNC_QUEUE = True

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DEV_DATABASE_URL') or
        'sqlite:///' + os.path.join(database_dir, 'development.sqlite')
    )


class TestingConfig(Config):
    """Created in test setup, deleted in tear down."""
    TESTING = True
    IS_ASYNC_QUEUE = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DEV_DATABASE_URL') or
        'sqlite:///' + os.path.join(database_dir, 'testing.sqlite')
    )


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        'sqlite:///' + os.path.join(database_dir, 'production.sqlite')
    )


# If you change the keys of this dictionary, you need
# to change DATABASE comments of the templates (i.e. srt.yaml).
api_config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': TestingConfig,
}
