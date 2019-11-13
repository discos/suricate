from __future__ import with_statement
import os
import sys
import logging
import yaml


suricate_dir = os.path.join(os.getenv('HOME'), '.suricate')
config_dir = os.path.join(suricate_dir, 'config')
config_file  = os.path.join(config_dir, 'config.yaml')
log_dir = os.path.join(suricate_dir, 'logs')

# --- CREATE FILES AND DIRECTORIES
try:  
    os.mkdir(suricate_dir)
except OSError:
    pass  # The directory already exists
try:  
    os.mkdir(config_dir)
except OSError:
    pass  # The directory already exists
try:  
    os.mkdir(log_dir)
except OSError:
    pass  # The directory already exists


default_config = { 
    'COMPONENTS': {
        "TestNamespace/Positioner00": {
            'properties': [
                {"name": "position", "timer": 0.1},
                {"name": "current", "timer": 0.1}
            ],
            'methods': [
                {"name": "getPosition", "timer": 0.1},
            ],
        },
        "TestNamespace/Positioner01": {
            "properties": [
                {"name": "current", "timer": 0.1}
            ],
        } 
    },

    'SCHEDULER': {
        'RESCHEDULE_INTERVAL': 5,  # Seconds
        'RESCHEDULE_ERROR_INTERVAL': 10,  # Seconds
    },

    'HTTP': {
        'port': 5000,  # Web app port
        'baseurl': 'http://127.0.0.1',  # Web app URL
    },
}


# ---- LOGGING CONFIGURATION
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
aps_logfile = os.path.join(log_dir, 'apscheduler.log')
aps_handler = logging.FileHandler(aps_logfile)
aps_handler.setFormatter(formatter)
logging.getLogger('apscheduler').addHandler(aps_handler)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

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
except IOError:
        print 'INFO: Using the default configuration'
        config = default_config
