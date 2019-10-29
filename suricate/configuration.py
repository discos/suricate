import sys
import os

confdir = os.path.join(os.getenv('HOME'), '.suricate')
try:
    sys.path.insert(0, confdir)
    # Import all attributes from the config files:
    # COMPONENTS, RESCHEDULE_ERROR_TIME 
    from config import *
except ImportError, ex:
    print('ERROR: %s.' % ex)
    print('Please run the suricate-config command in order to')
    print('create the %s/config.py file.' % confdir)
    sys.exit(1)
finally:
    sys.path.remove(confdir)
