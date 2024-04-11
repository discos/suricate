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
r = redis.StrictRedis(decode_responses=True)


def ps_output(keyword):
    result = ''
    cmd = f'ps aux | grep {keyword}'
    if RUN_ON_MANAGER_HOST is True:
        result = subprocess.check_output(cmd, shell=True)
    else:
        key = '__manager_connection/error'
        try:
            # pylint: disable=import-error
            from Acspy.Util.ACSCorba import getManagerHost
            # pylint: enable=import-error
            with subprocess.Popen(
                    ['ssh', '-T', f'discos@{getManagerHost()}'],
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=0
            ) as ssh_process:
                ssh_process.stdin.write(cmd + '\n')
                ssh_process.stdin.write("echo END\n")
                ssh_process.stdin.write("logout\n")
                ssh_process.stdin.close()
                for line in ssh_process.stdout:
                    if line == "END\n":
                        break
                    result += line
                r.delete(key)
        except:
            message = 'can not get information from manager'
            if r.get(key) != message:
                r.set(key, message)
                logger = logging.getLogger('suricate')
                logger.error(message)
            return ''
    return result.decode()


def is_container_online(name):
    return name in ps_output('StartContainer')


def is_manager_online():
    return 'maciManagerJ' in ps_output('maciManager')


def get_client_class():
    # pylint: disable=import-error
    from Acspy.Clients.SimpleClient import PySimpleClient
    # pylint: enable=import-error
    return PySimpleClient
