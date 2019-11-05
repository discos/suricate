import json
import datetime

import redis
from suricate.errors import CannotGetComponentError, ComponentAttributeError


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
    except CannotGetComponentError, ex:
        message = 'can not get %s ' % component.name
        data_dict.update({'error': message})
        raise CannotGetComponentError(message)
    except AttributeError, ex:
        message = str(ex)
        data_dict.update({'error': message})
        raise ComponentAttributeError(message)
    finally:
        r = redis.StrictRedis()
        r.hmset(channel, data_dict)
        r.publish(channel, json.dumps(data_dict))
        healthy_job_key = 'healthy_job:%s' % channel
        r.set(healthy_job_key, 1)
