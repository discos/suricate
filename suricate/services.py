from __future__ import print_function, unicode_literals
import subprocess
import threading
import logging
import redis

logging_lock = threading.Lock()
r = redis.StrictRedis()

def get_container_list():
    key = '__manager_connection/error'
    try:
        from Acspy.Util.ACSCorba import getManagerHost
        ssh_process = subprocess.Popen(
            ['ssh', '-T', 'discos@%s' % getManagerHost()],
            stdin=subprocess.PIPE, 
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            universal_newlines=True,
            bufsize=0
        )   
        ssh_process.stdin.write("acsContainersStatus\n")
        ssh_process.stdin.write("echo END\n")
        ssh_process.stdin.write("logout\n")
        ssh_process.stdin.close()
        output_lines = []
        for line in ssh_process.stdout:
            if line == "END\n":
                break
            else:
                output_lines.append(line)
        r.delete(key)
        return output_lines
    except Exception:
        message = 'can not get information from manager'
        if r.get(key) != message:
            r.set(key, message)
            logger = logging.getLogger('suricate')
            logging.error(message)
        return []
    

def is_container_online(name):
    for line in get_container_list():
        if ('%s container is running' % name) in line:
            return True
    return False


mng_online_cmd = """python -c "from __future__ import print_function;
from Acspy.Util.ACSCorba import getManager;
print('yes', end='') if getManager() else print('no', end='')" """
def is_manager_online():
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


def get_client_class():
    from Acspy.Clients.SimpleClient import PySimpleClient
    return PySimpleClient
