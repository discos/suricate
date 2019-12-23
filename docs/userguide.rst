.. _user-guide:

**********
User Guide
**********

.. topic:: Preface

   There are two ways to get the antenna parameters: by using a Redis
   client and by a HTTP REST API.  This documentation only mentions the
   former one, because the HTTP API is still under development.


How to get the antenna parameters
=================================
The :download:`SRT configuration file <../templates/srt.yaml>` contains all
parameters you can get. Have a look at its first 20 lines:

.. literalinclude:: ../templates/srt.yaml
   :language: yaml
   :lines: 1-20
   :linenos:

Basically there is a list of *components*, and in the previous lines you only
see the ``ANTENNA/Boss`` one.  Each component has some parameters (*properties*
or *methods*) that you can ask for. They are identified by the lable
``name``, it means, regarding to the previous lines, you can get the following
``ANTENNA/Boss`` parameters: ``rawAzimuth``, ``rawElevation``, ``observedAzimuth``,
``observedElevation``.

To get them you need:

#. a Redis client installed on your machine
#. a way to use your client in order to get the antenna parameters



Install a Redis client
----------------------
In this section we will briefly see how to install one of them for Python
and C, but if you do not use that languages, visit the
`official Redis webpage <https://redis.io/clients>`__ to get
the right client for your operating system and programming language.

Python
~~~~~~
The most used Python client is called `redis-py <https://pypi.org/project/redis/>`__.
To install it by ``pip``, simply:

.. code-block:: shell

   $ pip install redis

If you do not have ``pip``, then download the source files from the
`redis-py webpage <https://pypi.org/project/redis/>`__, extract them,
move to the source file directory and execute:

.. code-block:: shell

   $ python setup.py install


C Programming Language
~~~~~~~~~~~~~~~~~~~~~~
The official C client is available on the `Hiredis GitHub page
<https://github.com/redis/hiredis>`__. Clone it on your machine:

.. code-block:: shell

  $ git clone https://github.com/redis/hiredis.git

The installation steps depend of your operating system and compiler.
For instance, on Linux CentOS:

.. code-block:: shell

  $ cd hiredis/
  $ make
  $ sudo make install


Use your client to get the antenna parameters
---------------------------------------------
To get the antenna parameters you have to connect your client
to the Redis server.  Server IP and port are ``192.168.200.207``
and ``6379``. That is not enough, because you need to understand
how your client works. These instructions should be
provided by your Redis client documentation. Let's see two examples,
using Python and C. Please read the :ref:`python_client` section
also if you want to use the C programming language, because the
Python examples show you all information (the :ref:`c_client` section
is just a short summary).


.. _python_client:

How to use the Python client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Let's see how to get the ``rawAzimuth`` from a Python shell:

.. code-block:: python

   >>> from redis import StrictRedis # Import the redis client
   >>> r = StrictRedis(host='192.168.10.207', port=6379)  # Connect to server
   >>> r.hgetall('ANTENNA/Boss/rawAzimuth')  # Ask for the rawAzimuth parameter
   {
     'units': 'radians', 'timestamp': '2019-12-18 12:52:04.206445',
     'description': 'raw azimuth (encoder value), without any correction',
     'value': '0.602314332058', 'error': ''
   }

As you can see, to get a parameter you use a key made by the
component name (``ANTENNA/Boss``) and the parameter name
(``rawAzimuth``): ``ANTENNA/Boss/rawAzimuth``.  The result of the
request contains the value of the property, its units, description
and timestamp.  In case of error there is an error message, and the
``value`` is an empty string:

.. code-block:: python

   >>> r.hgetall('ANTENNA/Boss/rawAzimuth')
   {
     'units': 'radians', 'timestamp': '2019-12-18 12:55:13.197819',
     'description': 'raw azimuth (encoder value), without any correction',
     'value': '', 'error': 'component ANTENNA/Boss not available'
   }


Here is how to get a particular field:

.. code-block:: python

   >>> result = r.hgetall('ANTENNA/Boss/rawAzimuth')
   >>> result['units']
   'radians'
   >>> result['value']
   '0.599527371772'
   >>> result['description']
   'raw azimuth (encoder value), without any correction'

Another way is to use the ``hget()``, giving the field name
as a second argument:

.. code-block:: python

   >>> r.hget('ANTENNA/Boss/rawAzimuth', 'value')
   '0.598923921358'


.. note:: The Python ``hgetall()`` and ``hget()`` methods execute the
   Redis calls `HGETALL <https://redis.io/commands/hgetall>`__ and
   `HGET <https://redis.io/commands/hget>`__.

To know the status of the components (``available`` or ``unavailable``) use
the key ``components``:

.. code-block:: python

   >>> r.hgetall('components')
   {
     'MANAGEMENT/Gavino': 'available', 'WEATHERSTATION/WeatherStation': 'available',
     'RECEIVERS/SRTKBandMFReceiver': 'available', 'RECEIVERS/SRT7GHzReceiver': 'available',
     'ANTENNA/Boss': 'available', 'RECEIVERS/Boss': 'available'
   }


.. _c_client:

How to use the C client
~~~~~~~~~~~~~~~~~~~~~~~
To understand how to get the ``rawAzimuth`` parameter look at the
most important lines of :download:`example.c <examples/example.c>`
source file:

.. literalinclude:: examples/example.c
   :language: c
   :lines: 39-54
   :linenos:

If you compile :download:`example.c <examples/example.c>` and execute the
program, then you get the following output:

.. code-block:: shell

   $ gcc example.c -I /usr/local/include/hiredis/ -lhiredis  # Linux CentOS
   $ ./a.out

   HGETALL ANTENNA/Boss/rawAzimuth
   * description: raw azimuth (encoder value), without any correction
   * error:
   * units: radians
   * timestamp: 2019-12-18 16:19:50.042722
   * value: 0.469729642021

   HGET ANTENNA/Boss/rawAzimuth value: 0.469729642021

For more information about the Redis C client please scroll down the
`C client website page <https://github.com/redis/hiredis>`__.


Public and subscribe
====================
We saw how to ask for antenna parameters in a *request-response* manner.
Using that pattern you have to take care of the result, because you
can get the same value for different requests.
For intance, if you look at the :download:`SRT configuration file
<../templates/srt.yaml>` you see that ``rawAzimuth`` has a sampling time of 400ms.
That is why if you ask for the parameter faster than 400ms you get the same result
for different requests:

.. code-block:: python

   >>> import time
   >>> import redis
   >>> r = redis.StrictRedis(host='192.168.10.207', port=6379)
   ...     print(r.hgetall('ANTENNA/Boss/rawAzimuth')['timestamp'])
   ...     time.sleep(0.2)  # 200ms
   ...
   2019-12-20 12:11:48.443357
   2019-12-20 12:11:48.842924
   2019-12-20 12:11:48.842924
   2019-12-20 12:11:49.246206
   2019-12-20 12:11:49.246206

As you can see by looking at these timestamps, the second result is
the same as the third, and the forth is the same as the fifth. It is
not a big issue, because you can discard the result in case its
timestamp is the same as the previous response. But there is
another way: the *public-subscribe* pattern.  In that case you
subscribe to a channel and wait for new data.
Let'see how to do it by examples, using the Python client.

As a first step we create a *pubsub* object and subscribe it
to the ``ANTENNA/Boss/rawAzimuth`` channel:

.. code-block:: python

   >>> import redis
   >>> r = redis.StrictRedis(host='192.168.10.207', port=6379)
   >>> pubsub = r.pubsub()
   >>> pubsub.subscribe('ANTENNA/Boss/rawAzimuth')

Now we are ready to get the messages. The first one is a kind of header
that tell us which channel we are listening from.  Its ``type``
is ``subscribe``:

.. code-block:: python

   >>> pubsub.get_message()
   {
     u'pattern': None, u'type': 'subscribe',
     u'channel': 'ANTENNA/Boss/rawAzimuth', u'data': 1L
   }

From now on the ``type`` of the messages is ``message``, and that
means they contain the antenna parameter:

.. code-block:: python

   >>> pubsub.get_message()
   {
     u'pattern': None, u'type': 'message', u'channel': 'ANTENNA/Boss/rawAzimuth',
     u'data': '{
       "description": "raw azimuth (encoder value), without any correction",
       "error": "", "units": "radians", "timestamp": "2019-12-20 14:43:16.262544",
       "value": "3.97375753112"
     }'
   }

The ``pubsub`` has a method ``listen()`` that waits for new
messages. In fact, as you can see in the following example, we
do not get the same message on different responses, as appened
in the *request-response* pattern:

.. code-block:: python

    ... for item in pubsub.listen():
    ...     if item['type'] == 'message':
    ...         data = json.loads(item['data'])
    ...         timestamp = data.get('timestamp')
    ...         value = data.get('value')
    ...         print(timestamp, value)
    ...
    (u'2019-12-20 15:04:23.648343', u'4.07524413623')
    (u'2019-12-20 15:04:24.043550', u'4.07527853477')
    (u'2019-12-20 15:04:24.465494', u'4.07530617372')
    (u'2019-12-20 15:04:24.843325', u'4.07533925004')
    (u'2019-12-20 15:04:25.246359', u'4.07536964412')

.. note:: The antenna parameter is stored as a json string in the
   ``data`` field of the item.  I used ``json.loads()`` in order
   to convert the json string to a Python dictionary.

You can subscribe to more than one channel at the same time:

.. code-block:: python

   ... pubsub = r.pubsub()
   ... pubsub.subscribe(
   ...       'ANTENNA/Boss/rawAzimuth',
   ...       'ANTENNA/Boss/rawElevation'
   ... )
   ... for item in pubsub.listen():
   ...     if item['type'] == 'message':
   ...         channel = item['channel']
   ...         data = json.loads(item['data'])
   ...         value = data.get('value')
   ...         print(channel, value)
   ...
   ('ANTENNA/Boss/rawAzimuth', u'0.758804232371')
   ('ANTENNA/Boss/rawElevation', u'0.659474554184')
   ('ANTENNA/Boss/rawAzimuth', u'0.758810651617')
   ('ANTENNA/Boss/rawElevation', u'0.659490653912')
   ('ANTENNA/Boss/rawElevation', u'0.659506753743')
                         ...


You can also use the *glob* syntax. It means you can use a
``*`` to listen from more than one channel. For insance, in the following
case we are listening to all channels starting with ``ANTENNA/Boss``:

.. code-block:: python

   ... pubsub = r.pubsub()
   ... pubsub.psubscribe('ANTENNA/Boss/*')
   ... for item in pubsub.listen():
   ...     if item['type'] == 'pmessage':
   ...         channel = item['channel']
   ...         data = json.loads(item['data'])
   ...         value = data.get('value')
   ...         print(channel, value)
   ...
   ('ANTENNA/Boss/observedDeclination', u'0.952583014116')
   ('ANTENNA/Boss/observedAzimuth', u'0.800302875968')
   ('ANTENNA/Boss/rawElevation', u'0.668070294866')
   ('ANTENNA/Boss/observedElevation', u'0.666206037338')
   ('ANTENNA/Boss/rawAzimuth', u'0.762179742186')
   ('ANTENNA/Boss/observedRightAscension', u'0.929348150783')
   ('ANTENNA/Boss/observedGalLongitude', u'2.53064537516')
   ('ANTENNA/Boss/observedGalLatitude', u'-0.0212982297497')
   ('ANTENNA/Boss/status', u'MNG_OK')
   ('ANTENNA/Boss/observedAzimuth', u'0.800308445826')
                           ...

.. note:: In the last example (glob syntax) We subcribed to the channels
   using ``pubsub.psubscribe()``  and not ``pubsub.subscribe()``.
   We also wait for the type ``pmessage`` and not ``message``.
