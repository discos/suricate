
import subprocess
import threading
import logging
import redis
 
# If you import config from suricate.configuration to check
# config['RUN_ON_MANAGER_HOST'] then ps_output() will block
# in case the manager is online. I temporarily define the
# parameter here, waiting for a better idea.
RUN_ON_MANAGER_HOST = True

logging_lock = threading.Lock()
r = redis.StrictRedis()


def ps_output(keyword):
    result = ''
    cmd = 'ps aux | grep %s' % keyword
    if RUN_ON_MANAGER_HOST is True:
        result = subprocess.check_output(cmd, shell=True)
    else:
        key = '__manager_connection/error'
        try:
            from Acspy.Util.ACSCorba import getManagerHost
            ssh_process = subprocess.Popen(
                ['ssh', '-T', 'discos@%s' % getManagerHost()],
                shell=True,
                stdin=subprocess.PIPE, 
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                universal_newlines=True,
                bufsize=0
            )   
            ssh_process.stdin.write(cmd + '\n')
            ssh_process.stdin.write("echo END\n")
            ssh_process.stdin.write("logout\n")
            ssh_process.stdin.close()
            for line in ssh_process.stdout:
                if line == "END\n":
                    break
                else:
                    result += line
            r.delete(key)
        except Exception:
            message = 'can not get information from manager'
            if r.get(key) != message:
                r.set(key, message)
                logger = logging.getLogger('suricate')
                logging.error(message)
            return ''
    return result
    

def is_container_online(name):
    return name.encode('latin-1') in ps_output('StartContainer')


def is_manager_online():
    return b'maciManagerJ' in ps_output('maciManager')


def get_client_class():
    from Acspy.Clients.SimpleClient import PySimpleClient
    return PySimpleClient
