.. _user-guide:

**********
User Guide
**********

.. topic:: Preface

   There are two ways to get the antenna parameters: by using a Redis
   client and by a HTTP REST API.  This documentation only mentions the
   former one, because the HTTP API is still under development.


.. _prerequisites:

Prerequisites
=============
To get the antenna parameters you need to install a Redis client on your machine.
Visit the `official Redis webpage <https://redis.io/clients>`__ to choose and
download a client for your operating system and programming language.  Please also
read your clients documentation in order to understand how to install and use it.
For instance, if Python is your programming language, read the `redis-py client
documentation <https://pypi.org/project/redis/>`__.


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
#. the IP address of the Redis server you will connect to
#. to tell you client how to connect to the Redis server and
   get the parameters

If you have followed the instructions of previous section
(:ref:`prerequisites`) then you already have a Redis client installed
on your machine.
The server IP address is ``192.168.200.207``, so now you only need
to understand how your client works. These instructions should be
provided by your redis client documentation. Let's see two examples,
using Python and C. Please read the :ref:`python_client` section
also if you want to use the C programming language, because the
Python examples show you all information (the :ref:`c_client` section
is just a short summary).


.. _python_client:

Python client
-------------
Download the source files and install them, as explained in the `Python client webpage
`here <https://pypi.org/project/redis/>`__. Now you are ready to work.
Let's see how to get the ``rawAzimuth`` from a Python shell:

.. code-block:: python

   >>> import redis  # Import the redis client
   >>> r = redis.StrictRedis(host='192.168.10.207')  # Connect to the server
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
value is an empty string:

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

C client
--------
Download the redis C client form its `GitHub page <https://github.com/redis/hiredis>`__
and install it. For example, on a Linux CentOS distribution:

.. code-block:: shell

  $ $ git clone https://github.com/redis/hiredis.git
  $ cd hiredis/
  $ make
  $ sudo make install


Look how to get the ``rawAzimuth`` parameter by reading the
most important lines of :download:`example.c <examples/example.c>`
source file:

.. literalinclude:: examples/example.c
   :language: c
   :lines: 39-54
   :linenos:

If you compile :download:`example.c <examples/example.c>` and execute the
program you get the following output:

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
