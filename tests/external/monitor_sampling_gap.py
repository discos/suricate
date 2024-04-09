"""Example: 
   
   $ python suricate_gap.py -a WEATHERSTATION/WeatherStation/temperature -t 180

It write a logfile with the time diffence between two adjacent timestamps.
"""
import argparse
import logging
import time
from datetime import datetime

import redis


parser = argparse.ArgumentParser()
parser.add_argument(
    '-a',
    '--attribute',
    type=str,
    help='Attribute to be monitored',
    required=True
)
parser.add_argument(
    '-t',
    '--timer',
    type=int,
    help='Suricate sampling time of the attribute',
    required=True
)
args = parser.parse_args()


logging.basicConfig(
    filename='suricate_gap.log',
    filemode='w',
    format='%(name)s - %(levelname)s - %(message)s'
)

time_step = 10  # seconds
r = redis.StrictRedis(host='127.0.0.1', port=6379)

t0 = datetime.now()
prev_t = None
while True:
    data = r.hgetall(args.attribute)
    t = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
    if prev_t:
        delta = (t - prev_t).seconds
        elapsed_time = (t - t0).seconds
        max_allowed_delta = args.timer + 2*time_step
        if delta > max_allowed_delta:
            logging.error('delta time is %d seconds' % delta)
        else:
            if t != prev_t:
                msg = 'elapsed time: %d seconds' % elapsed_time
                print(msg)
                logging.info(msg)
                t0 = t
    prev_t = t
    time.sleep(time_step)
