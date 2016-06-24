.. _quickstart:

**********
Quickstart
**********

.. topic:: Preface

   This section is intended to be used as a quick introcution to Suricate.
   You will see how to install Suricate and configure the system (ACS and
   Suricate itself), and eventually how to read the property values.
   At the end of the section you will be able to use Suricate for most
   of its use cases. For more details about the configuration and the
   Suricate architecture, look respectively at the :ref:`user-guide` and
   :ref:`dev-guide` sections.


How to install Suricate
=======================

Prerequisite
------------
To use Suricate, you need to have `ACS <https://github.com/ACS-Community/ACS>`_
and `Redis <http://redis.io/>`_ installed on your machine.
The ACS version must have Python >= 2.6.


Installation
------------
You can install Suricate by means of 
`pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_,
the official Python package manager:

.. code-block:: shell

    $ pip install git+https://github.com/marco-buttu/suricate.git

This command will install Suricate and its dependencies:
`APScheduler <https://apscheduler.readthedocs.org>`_, a `Python interface to
Redis <https://pypi.python.org/pypi/redis>`_, and
`Flask <http://flask.pocoo.org/>`_.
In case pip is not installed on your machine, you can manually install
Suricate in the following way:

.. code-block:: shell

   $ git clone https://github.com/marco-buttu/suricate.git
   $ cd suricate/
   $ python setup.py install


How to use Suricate
===================
In this chapter we will see how to use Suricate in a real scenario.
Before starting, we need to set up the ACS environment, and then we will
run the Redis server and evantually Suricate.

ACS environment
---------------
Let's suppose we want to monitor the properties of some ``Positioner`` components.
We need to have an ACS introot, an ACS CDB, the ``Positioner`` IDL interface
and its related implementation class. All but the introot are contained in the
:file:`suricate/tests/acsenv` directory:

.. code-block:: bash

    $ ls
    setenv.sh  CDB  components

The ``Positioner`` component is contained in the :file:`components`
directory. Its implementation is located in :file:`components/src`:

.. code-block:: bash

    $ ls components/src/
    Makefile  Positioner

The CDB defines 5 different configurations of the ``Positioner`` class, which
live in the ``mynamespace`` namespace:

.. code-block:: bash

    $ ls CDB/alma/mynamespace/
    Positioner  Positioner00  Positioner01  Positioner02  Positioner03

This means we can instantiate 5 ``Positioner`` components at the same time,
called ``Positioner``, ``Positioner00``, ..., ``Positioner03``.

The :file:`suricate/tests/acsenv/setenv.sh` bash script, if executed
with the ``introot`` argument, creates the introot directory (in case it
does not yet exist), and sets the ``INTROOT`` and ``ACS_CDB`` environment
variables:

.. code-block:: bash

    $ source setenv.sh introot
    Creating the INTROOT to /.../acsenv/introot
    ......
    ACS introot and CDB properly configured.
    $ echo $ACS_CDB
    /home/marco/webles/suricate/tests/acsenv
    $ echo $INTROOT
    /home/marco/webles/suricate/tests/acsenv/introot

To install the ``Positioner`` class component, we have to execute the 
:file:`suricate/tests/acsenv/setenv.sh` bash script, with the ``install``
argument:

.. code-block:: bash

    $ source setenv.sh install
    ......
    OK, you are ready to run ACS :)

If you want to open a new shell, in order to use ACS, you have to run
the :file:`setenv.sh` script in that shell too, without any argument:

.. code-block:: bash

    $ source setenv.sh  # New shell
    ACS introot and CDB properly configured.

In the same shell you executed :file:`setenv.sh`, run the ``acsStart`` command:

.. code-block:: bash

    $ acsStart
    ......
    [acsStart] ACS is up and running

We also need to run the ``PositionerContainer``. In the same shell (or
in a new one, after executing :file:`setenv.sh`), execute the following
command:

.. code-block:: bash

    $ acsStartContainer -py PositionerContainer
    ......
    ContainerStatusMsg: Ready

The ACS environment is now configured and ready to load the ``Positioner``
components.


Run Redis server
----------------
To run the Redis server, open a new shell and execute the
``redis-server`` command:

.. code-block:: bash

    $ redis-server
    ......
    The server is now ready to accept connections on port 6379


Suricate execution
------------------
As we said in the section :ref:`motivations`, Suricate 
is an application that reads the properties of some ACS components
in order to publish and save them via `Redis <http://redis.io/>`_. 
This means we need to tell Suricate which properties we want it to
read. We can do this in real time, by using the Suricate HTTP API,
or statically, by using a configuration file. In this quick start
we only see the latter method. If you want to use the Suricate HTTP
API, take a look at the :ref:`user-guide` section.

Configuration
~~~~~~~~~~~~~
The command  ``suricate-config`` creates a Suricate configuration
file:

.. code-block:: bash

    $ suricate-config
    /home/marco/.suricate/config.py created!

This is a template file, that you can modify in order to indicate the
properties you want to monitor. Let's have a look at it::

    COMPONENTS = { 
        "mynamespace/Positioner00": [
            {"name": "position", "timer": 0.1},
            {"name": "current", "timer": 0.1}],
        "mynamespace/Positioner01": [
            {"name": "current", "timer": 0.1}],
    }

There is a Python dictionary, called ``COMPONENTS``. Its keys are the components
names, and the values are a list of properties, represented as a dictionary.
The file showed above, created by ``suricate-config``,  is the configuration
file we will use during the tests. Using this file, Suricate will monitor two
properties of the
component ``mynamespace/Positioner00``, named ``position`` and ``current``, and
one property of ``mynamespace/Positioner01``, named ``current``. The frequency
sampling is the same for all properties: 0.1 seconds. 

Run Suricate
~~~~~~~~~~~~
If we execute the ``suricate-server`` command, then Suricate starts reading the
properties, saving their values in the Redis DB, and also publishing the
values in a Redis channel.

.. note:: To read a property, Suricate starts a job over that property, so we
   have one job per property. In :ref:`dev-guide` we will see in detail what a
   job is.

At this point, we can:

* get (using the Suricate HTTP API) the list of active jobs
* get the properties values using a redis client


How to get the list of active jobs
==================================
You can get the list of active jobs performing an HTTP GET request at
`<http://localhost:5000/publisher/api/v0.1/jobs>`__.
Here is an example using curl:

.. code-block:: shell

    $ curl http://localhost:5000/publisher/api/v0.1/jobs
    {
      "jobs": [
        {
          "id": "mynamespace/Positioner00/position", 
          "timer": 0.10000000000000001
        }, 
        {
          "id": "mynamespace/Positioner00/current", 
          "timer": 0.10000000000000001
        }, 
        {
          "id": "mynamespace/Positioner01/current", 
          "timer": 0.10000000000000001
        }
      ]
    }


You can also do it programmatically, using the
programming language of your choice.  Here is an example using Python and
the third-party `requests <http://docs.python-requests.org/>`__ library:

.. doctest::

    >>> import requests
    >>> resp = requests.get('http://localhost:5000/publisher/api/v0.1/jobs')
    >>> jobs = resp.json()['jobs']
    >>> for job in jobs:
    ...     print(job['id'], job['timer'])
    ... 
    (u'mynamespace/Positioner00/position', 0.10000000000000001)
    (u'mynamespace/Positioner00/current', 0.10000000000000001)
    (u'mynamespace/Positioner01/current', 0.10000000000000001)


Get the properties values using a Redis client
==============================================
You can retrieve the properties values by means of
a Redis client. There are clients for almost every programming
language. Look at `<http://redis.io/clients>`__ for a full list.
In this section, we will see some examples using Python and the
`redis-py <https://github.com/andymccurdy/redis-py>`__ third-party library.

The request/response and the publish subscribe paradigms are
both supported. To use the request/response paradigm, call the
Redis' ``get`` command::

    >>> from redis import StrictRedis
    >>> r = StrictRedis()
    >>> r.get('mynamespace/Positioner00/position')
    '0.0 @ 2016-06-14 10:36:58.393272'
    >>> r.get('mynamespace/Positioner00/current')
    '0.0 @ 2016-06-14 10:37:05.495497'
    >>> r.get('mynamespace/Positioner01/current')
    '0.0 @ 2016-06-14 10:37:35.238080'

The Redis key is the job identifier, and the value is the last value of the property.
In this example, the values are all ``0.0``. The value and the timestamp are
separated by a ``@``. If the key refers to a not monitored property,
you get ``None``::

    >>> r.get('mynamespace/Positioner01/foo')
    >>>

Using the publish/subscribe paradigm, you can get all the values published
for a property, starting from the time you subscribe to the channel.
Here is an example:: 

    >>> import redis
    >>> client = redis.StrictRedis()
    >>> pubsub = client.pubsub()
    >>> pubsub.subscribe('mynamespace/Positioner01/current')
    >>> pubsub.get_message()
    {'pattern': None, 'type': 'subscribe',
    'channel': 'mynamespace/Positioner01/current', 'data': 1L}
    >>> pubsub.get_message()
    {'pattern': None, 'type': 'message',
    'channel': 'mynamespace/Positioner01/current',
    'data': '{"error": false, "timestamp": "2016-06-14 11:21:40.394367",
    "message": "", "value": 0.0}'}
    >>> pubsub.get_message()
    {'pattern': None, 'type': 'message',
    'channel': 'mynamespace/Positioner01/current',
    'data': '{"error": false, "timestamp": "2016-06-14 11:21:40.441427",
    "message": "", "value": 0.0}'}
    >>> pubsub.get_message()


The first message returned by ``pubsub.get_message()`` is the
subscribe confirmation message.
Notice you do not get the last value of the property. You get the values
published, one by one, in a chronological way.

You can also subscribe to more than one channel::

    >>> client = redis.StrictRedis()
    >>> pubsub = client.pubsub()
    >>> pubsub.subscribe(
    ...     'mynamespace/Positioner00/position',
    ...     'mynamespace/Positioner00/current')
    >>> pubsub.get_message()
    {'pattern': None, 'type': 'subscribe',
    'channel': 'mynamespace/Positioner00/position', 'data': 1L}
    >>> pubsub.get_message()
    {'pattern': None, 'type': 'subscribe',
    'channel': 'mynamespace/Positioner00/current', 'data': 2L}
    >>> pubsub.get_message()
    {'pattern': None, 'type': 'message',
    'channel': 'mynamespace/Positioner00/current',
    'data': '{"error": false, "timestamp": "2016-06-14 12:54:54.098538",
    "message": "", "value": 0.0}'}
    >>> pubsub.get_message()
    {'pattern': None, 'type': 'message',
    'channel': 'mynamespace/Positioner00/position',
    'data': '{"error": false, "timestamp": "2016-06-14 12:54:54.098063",
    "message": "", "value": 0.0}'}

An easy way to subscribe to more then one channel at once, is using a
sort of wildcard, called *pattern*::

    >>> client = redis.StrictRedis()
    >>> pubsub = client.pubsub()
    >>> pubsub.psubscribe('mynamespace/Positioner*')
    >>> pubsub.get_message()
    {'pattern': None, 'type': 'psubscribe',
    'channel': 'mynamespace/Positioner*', 'data': 1L}
    >>> pubsub.get_message()
    {'pattern': 'mynamespace/Positioner*', 'type': 'pmessage',
    'channel': 'mynamespace/Positioner00/position',
    'data': '{"error": false, "timestamp": "2016-06-14 12:59:17.986962",
    "message": "", "value": 0.0}'}
    >>> pubsub.get_message()
    {'pattern': 'mynamespace/Positioner*', 'type': 'pmessage',
    'channel': 'mynamespace/Positioner00/current',
    'data': '{"error": false, "timestamp": "2016-06-14 12:59:17.987194",
    "message": "", "value": 0.0}'}
    >>> pubsub.get_message()
    {'pattern': 'mynamespace/Positioner*', 'type': 'pmessage',
    'channel': 'mynamespace/Positioner01/current',
    'data': '{"error": false, "timestamp": "2016-06-14 12:59:17.987102",
    "message": "", "value": 0.0}'}

Summary
=======
To summarize, once the ACS containers are ready and Suricate configured, you
only have to execute ``redis-server`` and ``suricate-server``. At this point
you will be able to read the properties values either from the Redis DB or from
the associated Redis channel.
