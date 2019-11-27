import time
import subprocess
import pytest


def test_run_only_once(capsys):
    """Only one instance of suricate must be running"""
    try:
        p1 = subprocess.Popen(['suricate-server', 'start'], stdout=subprocess.PIPE)
        time.sleep(1.5)
        p2 = subprocess.Popen(['suricate-server', 'start'], stdout=subprocess.PIPE)
        time.sleep(1.5)
        out, err = p2.communicate()
        assert out.startswith('ERROR: suricate is already running')
    finally:
        subprocess.call(['suricate-server', 'stop'])


if __name__ == '__main__':
    pytest.main()
