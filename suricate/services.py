import subprocess
import redis


mng_online_cmd = """python -c "from __future__ import print_function;
from Acspy.Util.ACSCorba import getManager;
print('yes', end='') if getManager() else print('no', end='')" """
def is_manager_online():
    r = redis.StrictRedis()
    any_available = False
    for status in r.hgetall('components').values():
        if status == 'unavailable':
            continue
        else:
            any_available = True
            break

    if any_available:
        return True
    else:
        result = subprocess.check_output(mng_online_cmd, shell=True)
        return True if result == 'yes' else False
