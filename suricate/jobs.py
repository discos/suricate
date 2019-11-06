import json
import datetime
import logging

import redis
from suricate.errors import CannotGetComponentError, ComponentAttributeError


logger = logging.getLogger('suricate')


def acs_property_publisher(channel, component, property_name):
    """Get the component reference and a property as a dict object."""
    value_dict = {'value': '', 'timestamp': str(datetime.datetime.now())}
    data_dict = dict(error='', **value_dict)
    try:
        prefix = component.device_attribute_prefix
        get_property_obj = getattr(component, prefix + property_name)
        property_obj = get_property_obj()
        value, comp = property_obj.get_sync()
        epoch = (comp.timeStamp - 122192928000000000) / 10000000.
        t = datetime.datetime.fromtimestamp(epoch)
        value_dict = {'value': value, 'timestamp': str(t)}
        data_dict.update(value_dict)
    except CannotGetComponentError:
        message = 'cannot get component %s' % component.name
        data_dict.update({'error': True, 'message': message})
        logger.error(message)
        raise CannotGetComponentError(message)
    except AttributeError:
        message = 'cannot get %s from %s' % (property_name, component.name)
        data_dict.update({'error': True, 'message': message})
        logger.error(message)
        raise ComponentAttributeError(message)
    finally:
        r = redis.StrictRedis()
        r.hmset(channel, data_dict)
        r.publish(channel, json.dumps(data_dict))
        healthy_job_key = 'healthy_job:%s' % channel
        r.set(healthy_job_key, 1)
