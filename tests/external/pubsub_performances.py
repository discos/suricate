"""The goal of this test is to check the apscheduler and redis performances,
and it is ACS-independent.

This is not an automatic test. It passes depending of the load and the
hardware of the machine that executes the tests.

It passes on a VM with 4GB of RAM, without ACS or any other heavy application
in execution, using:

   - delta_time=0.01
   - total_time=5

"""

import datetime
import logging
import time

import redis
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig()


def publisher(channel):
    r = redis.StrictRedis(decode_responses=True)
    r.publish(channel, 'from publisher...')


def get_from(func, channel, delta_time, total_time):
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=func,
            name='test',
            args=(channel,),
            trigger='interval',
            seconds=delta_time)

        r = redis.StrictRedis(decode_responses=True)
        pubsub = r.pubsub()
        pubsub.subscribe('test-channel')
        scheduler.start()
        t0 = datetime.datetime.now()
        messages = []
        while True:
            message = pubsub.get_message()
            delta = datetime.datetime.now() - t0
            delay = delta.seconds + float(delta.microseconds)/10**6
            if message:
                messages.append(message)
            if delay >= total_time:
                break
            time.sleep(delta_time/5.0)
        nmessages = len(messages) - 1  # No subscription
        expected = int(delay/delta_time)
        assert nmessages > expected*0.95
        print('\n')
        print('Number of messages: ', len(messages) - 1)  # No subscription
        print('Expected: ', int(delay/delta_time))
        print('messages[1]: ', messages[1])
        print('\n')
    finally:
        pubsub.unsubscribe()
        scheduler.shutdown()


if __name__ == '__main__':
    get_from(publisher, 'test-channel', 0.01, 5)
