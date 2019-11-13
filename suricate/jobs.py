import json
import datetime
import logging

import redis
from suricate.errors import CannotGetComponentError, ComponentAttributeError


logger = logging.getLogger('suricate')


def acs_publisher(channel, component, attribute):
    """Get the component reference and a property as a dict object."""
    value_dict = {'value': '', 'timestamp': str(datetime.datetime.utcnow())}
    data_dict = dict(error='', **value_dict)
    try:
        if hasattr(component, '_get_' + attribute):  # It is a property
            get_property_obj = getattr(component, '_get_' + attribute)
            property_obj = get_property_obj()
            value, comp = property_obj.get_sync()
            # TODO: check Acspy.Common.TimeHelper for right conversion
            epoch = (comp.timeStamp - 122192928000000000) / 10000000.
            t = datetime.datetime.fromtimestamp(epoch)
        else:  # It is a method, just call it
            t = datetime.datetime.utcnow()
            value = attribute_obj()
        value_dict = {'value': value, 'timestamp': str(t)}
        data_dict.update(value_dict)
    except CannotGetComponentError:
        message = 'cannot get component %s' % component.name
        data_dict.update({'error': message})
        logger.error(message)
        raise CannotGetComponentError(message)
    except AttributeError:
        message = 'cannot get attribute %s from %s' % (
                attribute, component.name)
        data_dict.update({'error': message})
        logger.error(message)
        raise ComponentAttributeError(message)
    except Exception, ex:
        message = 'cannot communicate with %s' % component.name
        data_dict.update({'error': message})
        logger.error(message)
        logger.debug(ex)
        raise CannotGetComponentError(message)
    finally:
        r = redis.StrictRedis()
        if not r.hmset(channel, data_dict):
            logger.error('cannot write data for %s' % channel)
        r.publish(channel, json.dumps(data_dict))
        healthy_job_key = 'healthy_job:%s' % channel
        if not r.set(healthy_job_key, 1):
            logger.error('cannot set %s' % healthy_job_key)
