from __future__ import print_function
import datetime
import logging
import time

import pytest

logging.basicConfig()


def test_get_all_messages(components, scheduler, pubsub):
    """Verify we get at least the 95% of the messages"""
    # We want each property value to be published every `iterval_time`
    # seconds, for a `total_time` number of seconds
    interval_time = 0.1
    total_time = 5  # Number of seconds we will publish
    properties = ('position', 'current')
    pubsub.psubscribe('test*')
    for component in components:
        for prop in properties:
            scheduler.add_attribute_job(
                component,
                prop,
                timer=interval_time,
                channel='test/%s/%s' % (component.name, prop))

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
        time.sleep(interval_time/(5.0 * len(components)))
    # Number of messages
    nmessages = len(messages) - 1   # Do not count the subscription message
    expected = len(components) * len(properties) * int(delay/interval_time)
    assert nmessages > expected*0.80  # Get at least the 80% of all messages

    print('\n')
    print('Number of messages: ', nmessages)
    print('Expected: ', expected)
    print('messages[1]: ', messages[1])
    print('\n')


if __name__ == '__main__':
    pytest.main()
