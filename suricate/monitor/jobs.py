import json
import logging
from datetime import datetime
import redis

import suricate.services
from suricate.configuration import dt_format
from suricate.errors import (
    CannotGetComponentError,
    ComponentAttributeError,
    ACSNotRunningError,
)


logger = logging.getLogger('suricate')
r = redis.StrictRedis(decode_responses=True)


def acs_publisher(
    channel,
    component,
    attribute,
    timer,
    units='',
    description=''
):
    """Get the component reference and a property as a dict object."""
    data_dict = {
        'value': '',
        'error': '',
        'timer': timer,
        'units': units,
        'description': description,
        'timestamp': datetime.utcnow().strftime(dt_format),
    }
    try:
        error_message = ''
        if component.name in component.unavailables:
            raise CannotGetComponentError()

        with suricate.services.logging_lock:
            startup_time = r.get(f'__{component.name}/startup_time')
            if startup_time:
                t = datetime.strptime(startup_time, dt_format)
                if datetime.utcnow() <= t:
                    message = \
                        f'{component.name} not ready: startup in progress'
                    data_dict.update({'error': message})
                    r.hset(
                        'components',
                        mapping={component.name: 'unavailable'}
                    )
                    key = f'__{component.name}/info'
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
        data_dict.update(
            {'value': value, 'timestamp': t.strftime(dt_format)}
        )
        # Update the components redis key
        with suricate.services.logging_lock:
            if r.hget('components', component.name) != 'available':
                message = f'OK - component {component.name} is online'
                key = f'__{component.name}/info'
                if r.get(key) != message:
                    logger.info(message)
                r.set(key, message)
                r.hset('components', mapping={component.name: 'available'})
                r.delete(f'__{component.name}/info')
            r.delete(f'__{component.name}/error')
    except CannotGetComponentError as ex:
        print(ex)
        if not suricate.services.is_manager_online():
            error_message = 'ACS not running'
            key = '__manager/error'
            Exc = ACSNotRunningError
            with suricate.services.logging_lock:
                r.delete(f'__{component.name}/error')
        else:
            error_message = f'cannot get component {component.name}'
            key = f'__{component.name}/error'
            Exc = CannotGetComponentError
            with suricate.services.logging_lock:
                r.delete('__manager/error')
        data_dict.update({'error': error_message})
        r.hset('components', mapping={component.name: 'unavailable'})
        raise Exc(error_message) from ex
    except AttributeError as ex:
        error_message = \
            f'cannot get attribute {attribute} from {component.name}'
        data_dict.update({'error': error_message})
        key = f'__{component.name}/error'
        r.hset('components', mapping={component.name: 'unavailable'})
        raise ComponentAttributeError(error_message) from ex
    except Exception as ex:
        logger.debug(str(ex))
        if not suricate.services.is_manager_online():
            error_message = 'ACS not running'
            key = '__manager/error'
            Exc = ACSNotRunningError
            with suricate.services.logging_lock:
                r.delete(f'__{component.name}/error')
        else:
            error_message = f'cannot get component {component.name}'
            key = f'__{component.name}/error'
            Exc = CannotGetComponentError
            with suricate.services.logging_lock:
                r.delete('__manager/error')
        data_dict.update({'error': error_message})
        r.hset('components', mapping={component.name: 'unavailable'})
        raise Exc(error_message) from ex
    finally:
        if error_message:
            with suricate.services.logging_lock:
                if r.get(key) != error_message:
                    logger.error(error_message)
                r.set(key, error_message)

        r.hset(channel, mapping=data_dict)
        r.publish(channel, json.dumps(data_dict))
        healthy_job_key = f'healthy_job:{channel}'
        if not r.set(healthy_job_key, 1):
            logger.error('cannot set %s', healthy_job_key)
