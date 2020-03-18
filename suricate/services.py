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


def is_container_online(client, comp_name):
    if client:  
        info = client.availableComponents(comp_name)
        if info:
            container_name = info[0].container_name
            result = subprocess.check_output('acsContainersStatus', shell=True)
            if ('%s container is running' % container_name) in result:
                return True
    return False


def get_client_class():
    from Acspy.Clients.SimpleClient import PySimpleClient
    return PySimpleClient
