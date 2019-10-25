import json
import datetime

from omniORB.CORBA import TRANSIENT, OBJECT_NOT_EXIST
from CORBA import COMM_FAILURE

import redis
from suricate.errors import CannotGetComponentError, ComponentAttributeError


def acs_property_publisher(channel, component, property_name):
    """Get the component reference and a property as a dict object."""
    value_dict = {'value': None, 'timestamp': str(datetime.datetime.now())}
    data_dict = dict(error=False, message='', **value_dict)
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
        data_dict.update({'error': True, 'message': str(ex)})
        raise
    except AttributeError, ex:
        message = str(ex)
        data_dict.update({'error': True, 'message': message})
        raise ComponentAttributeError(message)
    finally:
        r = redis.StrictRedis()
        value = value_dict['value']
        timestamp = value_dict['timestamp']
        r.set(channel, '%s @ %s' % (value, timestamp))
        r.publish(channel, json.dumps(data_dict))
