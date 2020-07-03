from __future__ import with_statement
import os
import sys
import logging
import yaml

from suricate.paths import  config_file, log_dir


# --- DEFAULT CONFIGURATION PARAMETERS
default_config = { 
    'COMPONENTS': {
        "TestNamespace/Positioner00": {
            'startup_delay': 0,
            'container': "PositionerContainer",
            'properties': [
                {
                    "name": "position",
                    "timer": 0.1,
                    "units": "mm",
                    "description": "current position",
                },
                {"name": "current", "timer": 0.1},
                {"name": "seq", "timer": 0.1},
            ],
            'methods': [
                {"name": "getPosition", "timer": 0.1},
                {"name": "getSequence", "timer": 0.1},
            ],
        },
        "TestNamespace/Positioner01": {
            'startup_delay': 0,
            "container": "PositionerContainer",
            "properties": [
                {"name": "current", "timer": 0.1}
            ],
        } 
    },

    'SCHEDULER': {
        'reschedule_interval': 1,  # Seconds
        'reschedule_error_interval': 2,  # Seconds
        'dbfiller_cycle': 1, # Seconds
    },

    'HTTP': {
        'port': 5000,  # Web app port
        'baseurl': 'http://127.0.0.1',  # Web app URL
    },

    'DATABASE': 'testing',

    'RUN_ON_MANAGER_HOST': True,

}


# Datetime string format
dt_format = "%Y-%m-%d~%H:%M:%S.%f"


# ---- LOGGING CONFIGURATION
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
aps_logfile = os.path.join(log_dir, 'apscheduler.log')
aps_handler = logging.FileHandler(aps_logfile)
aps_handler.setFormatter(formatter)
logging.getLogger('apscheduler').addHandler(aps_handler)
logging.getLogger('apscheduler').setLevel(logging.ERROR)
logging.getLogger('apscheduler').propagate = False
# logging.getLogger('apscheduler.scheduler').propagate = False

sur_logfile = os.path.join(log_dir, 'suricate.log')
sur_file_handler = logging.FileHandler(sur_logfile)
sur_file_handler.setFormatter(formatter)
sur_stream_handler = logging.StreamHandler(sys.stdout)
sur_stream_handler.setFormatter(formatter)
logging.getLogger('suricate').addHandler(sur_file_handler)
logging.getLogger('suricate').addHandler(sur_stream_handler)
logging.getLogger('suricate').setLevel(logging.INFO)


try:
    with open(config_file) as stream:
        config = yaml.safe_load(stream)
        if not config:
            config = default_config
except Exception, ex:
    config = default_config
    logger = logging.getLogger('suricate')
    logger.warning('cannot read %s: loading default config' % config_file)
