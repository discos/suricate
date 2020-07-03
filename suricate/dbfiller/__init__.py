import time
import logging
from datetime import datetime
from multiprocessing import Process

import redis
import sqlalchemy as db

from sqlalchemy.orm import sessionmaker
from suricate.models import Attribute
from suricate.api.config import api_config
from suricate.configuration import config, dt_format


logger = logging.getLogger('suricate')
r = redis.StrictRedis()

stop_key = '__dbfiller_stop'

class DBFiller(object):

    def __init__(self):
        r.set('__dbfiller_stop', 'no')

    def dbfiller(self):
        """Get all keys from redis and look for the attributes."""
        db_config = config['DATABASE']
        configuration_class = api_config[db_config]
        db_uri = configuration_class.SQLALCHEMY_DATABASE_URI
        engine = db.create_engine(db_uri)
        Attribute.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        while True:
            for key in r.scan_iter("*"):
                if key.startswith('_'):
                    continue
                elif ':' in key or 'healthy_job' in key:
                    continue
                elif key.count('/') != 2:
                    # Every attribute key has 2 slashes
                    # I.e. ANTENNA/Boss/rawAzimuth
                    continue
                else:
                    data = r.hgetall(key)
                    if  not isinstance(data, dict) and 'error' not in data:
                        continue
                    if 'timestamp' not in data:
                        continue
                    if data['error']:
                        continue  # Do not store error messages
    
                timestamp = datetime.strptime(data['timestamp'], dt_format)
                attr = Attribute(
                    id='{} @ {}'.format(key, data['timestamp']),
                    name=key,
                    units=data['units'],
                    timestamp=timestamp,
                    timer=data['timer'],
                    description=data['description'],
                    value=data['value'],
                    error=data['error'],
                )
                session = Session()
                session.add(attr)
                session.commit()
                session.close()

            time.sleep(config['SCHEDULER']['dbfiller_cycle'])
            if r.get('__dbfiller_stop') == 'yes':
                break

    def start(self):
        r.set('__dbfiller_stop', 'no')
        p = Process(target=self.dbfiller)
        p.daemon = False
        p.start()

    @classmethod
    def shutdown(cls):
        r.set('__dbfiller_stop', 'yes')
