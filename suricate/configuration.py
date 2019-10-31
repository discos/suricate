from __future__ import with_statement
import os
import yaml


default_config = { 
    'COMPONENTS': {
        "TestNamespace/Positioner00": [
            {"attribute": "position", "timer": 0.1},
            {"attribute": "current", "timer": 0.1}],
        "TestNamespace/Positioner01": [
            {"attribute": "current", "timer": 0.1}],
    },  

    'SCHEDULER': {
        'RESCHEDULE_INTERVAL': 5,  # Seconds
        'RESCHEDULE_ERROR_INTERVAL': 10,  # Seconds
    },

    'HTTP': {
        'port': 5000,  # Web app port
        'baseurl': 'http://127.0.0.1',  # Web app URL
    }
}


config_dir = os.path.join(os.getenv('HOME'), '.suricate')
config_file  = os.path.join(config_dir, 'config.yaml')
try:
    with open(config_file) as stream:
        config = yaml.safe_load(stream)
except IOError:
        print 'INFO: Using the default configuration'
        config = default_config
