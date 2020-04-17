import json
import logging
from datetime import datetime

import redis
import suricate.services
from suricate.errors import (
    CannotGetComponentError,
    ComponentAttributeError,
    ACSNotRunningError,
)


logger = logging.getLogger('suricate')
r = redis.StrictRedis()


def acs_publisher(channel, component, attribute, units='', description=''):
    """Get the component reference and a property as a dict object."""
    data_dict = {
        'value': '',
        'error': '',
        'units': units,
        'description': description,
        'timestamp': str(datetime.utcnow()),
    }
    try:
        error_message = ''
        if component.name in component.unavailables:
            raise CannotGetComponentError()

        with suricate.services.logging_lock:
            startup_time = r.get('__%s/startup_time' % component.name)
            if startup_time:
                t = datetime.strptime(startup_time, "%Y-%m-%d %H:%M:%S.%f")
                if datetime.utcnow() <= t:
                    message = '%s not ready: startup in progress' % component.name
                    data_dict.update({'error': message})
                    r.hmset('components', {component.name: 'unavailable'})
                    key = '__%s/info' % component.name
                    if r.get(key) != message:
                        logger.info(message)
                    r.set(key, message)
                    return

        if hasattr(component, '_get_' + attribute):  # It is a property
            get_property_obj = getattr(component, '_get_' + attribute)
            property_obj = get_property_obj()
            value, comp = property_obj.get_sync()
            # TODO: check Acspy.Common.TimeHelper for right conversion
            epoch = (comp.timeStamp - 122192928000000000) / 10000000.
            t = datetime.fromtimestamp(epoch)
        else:  # It is a method, just call it
            method = getattr(component, attribute)
            t = datetime.utcnow()
            value = method()
        if isinstance(value, list):
            value = tuple(value)  # Convert the value to a tuple
        value = str(value)
        data_dict.update({'value': value, 'timestamp': str(t)})
        # Update the components redis key
        with suricate.services.logging_lock:
            if r.hget('components', component.name) != 'available':
                message = 'OK - component %s is online' % component.name
                key = '__%s/info' % component.name
                if r.get(key) != message:
                    logger.info(message)
                r.set(key, message)
                r.hmset('components', {component.name: 'available'})
                r.delete('__%s/info' % component.name)
            r.delete('__%s/error' % component.name)
    except CannotGetComponentError:
        if not suricate.services.is_manager_online():
            error_message = 'ACS not running'
            key = '__manager/error'
            Exc = ACSNotRunningError
            with suricate.services.logging_lock:
                r.delete('__%s/error' % component.name)
        else:
            error_message = 'cannot get component %s' % component.name
            key = '__%s/error' % component.name
            Exc = CannotGetComponentError
            with suricate.services.logging_lock:
                r.delete('__manager/error')
        data_dict.update({'error': error_message})
        r.hmset('components', {component.name: 'unavailable'})
        raise Exc(error_message)
    except AttributeError:
        error_message = 'cannot get attribute %s from %s' % (
                attribute, component.name)
        data_dict.update({'error': error_message})
        key = '__%s/error' % component.name
        r.hmset('components', {component.name: 'unavailable'})
        raise ComponentAttributeError(error_message)
    except Exception, ex:
        if not suricate.services.is_manager_online():
            error_message = 'ACS not running'
            key = '__manager/error'
            Exc = ACSNotRunningError
            with suricate.services.logging_lock:
                r.delete('__%s/error' % component.name)
        else:
            error_message = 'cannot get component %s' % component.name
            key = '__%s/error' % component.name
            Exc = CannotGetComponentError
            with suricate.services.logging_lock:
                r.delete('__manager/error')
        data_dict.update({'error': error_message})
        r.hmset('components', {component.name: 'unavailable'})
        raise Exc(error_message)
    finally:
        if error_message:
            with suricate.services.logging_lock:
                if r.get(key) != error_message:
                    logger.error(error_message)
                r.set(key, error_message)

        if not r.hmset(channel, data_dict):
            logger.error('cannot write data on redis for %s' % channel)
        r.publish(channel, json.dumps(data_dict))
        healthy_job_key = 'healthy_job:%s' % channel
        if not r.set(healthy_job_key, 1):
            logger.error('cannot set %s' % healthy_job_key)
