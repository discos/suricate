from __future__ import print_function, unicode_literals
import subprocess
import logging
import redis

from Acspy.Util.ACSCorba import getManagerHost
logger = logging.getLogger('suricate')


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


def is_container_online(name):
    ssh_process = subprocess.Popen(
        ['ssh', '-T', 'discos@%s' % getManagerHost()],
        stdin=subprocess.PIPE, 
        stdout = subprocess.PIPE,
        universal_newlines=True,
        bufsize=0
    )   
    ssh_process.stdin.write("acsContainersStatus\n")
    ssh_process.stdin.write("echo END\n")
    ssh_process.stdin.write("logout\n")
    ssh_process.stdin.close()
    
    for line in ssh_process.stdout:
        if line == "END\n":
            break
        if ('%s container is running' % name) in line:
            return True

    return False



def get_client_class():
    from Acspy.Clients.SimpleClient import PySimpleClient
    return PySimpleClient
