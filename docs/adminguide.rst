.. _admin-guide:

**************************
System Administrator Guide
**************************

Architecture
============
The ``suricate-server`` is a Python application, composed of two parts:
a web application and a core.
The web application exposes an HTTP API to the clients. By means of this API
the clients can ask Suricate to monitor a property, get the list of
active jobs, and so forth.

To communicate with ACS, the web application
uses the *core* library, which gets the ACS properties values, saves them to
the in-memory database, and also publishes them in a channel where the clients
can subscribe to.

The clients get the properties values either reading from
the in-memory database or subscribing to the related channel. In the next
section we will see in detail how the core and the web
application are designed.

The core
--------
The core is basically a scheduler that executes some jobs periodically.
Every job has to:

#. read the value of its related property
#. set the value to the in-memory database
#. publish the value to a data channel

To better understand, take a look at the file :file:`config.py` we say
in the quickstart chapter::

    COMPONENTS = { 
        "TestNamespace/Positioner00": [
            {"name": "position", "timer": 0.1},
            {"name": "current", "timer": 0.1}],
        "TestNamespace/Positioner01": [
            {"name": "current", "timer": 0.1}],
    }

From this configuration, Suricate create tree jobs, one for each
property:

* ``TestNamespace/Positioner00/position``: executed every ``0.1`` seconds
  (``timer`` parameter), it reads the property ``position`` from the
  component ``Positioner00``, publishes the property
  value to a Redis channel and sets it to the in-memory database;
* ``TestNamespace/Positioner00/current``: executed every ``0.1`` seconds,
  it reads the property ``current`` from the component ``Positioner00``,
  publishes the property value to a Redis channel and sets it to the
  in-memory database;
* ``TestNamespace/Positioner00/current``: executed every ``0.1`` seconds,
  it reads the property ``current`` from the component ``Positioner01``,
  publishes the property value to a Redis channel and sets it to the
  in-memory database.

You can ask for the active jobs using an HTTP GET, as we saw in the
section quickstart-jobs:

.. code-block:: shell

    $ curl http://localhost:5000/publisher/api/v0.1/jobs
    {
      "jobs": [
        {
          "id": "TestNamespace/Positioner00/position", 
          "timer": 0.10000000000000001
        }, 
        {
          "id": "TestNamespace/Positioner00/current", 
          "timer": 0.10000000000000001
        }, 
        {
          "id": "TestNamespace/Positioner01/current", 
          "timer": 0.10000000000000001
        }
      ]
    }

A job is a thread that basically gets the property value
The period of execution is indicated by the ``timer`` attribute we say in
section quickstart-conf.


.. note:: The job is a thread, but APScheduler can be configured to
   choose the job executor you like more. You can use a thread pool, a process
   poll, asyncio, gevent, tornado, and twisted.



uses the third-part Python library
`APScheduler <https://apscheduler.readthedocs.io/>`_.

Error management
~~~~~~~~~~~~~~~~


The web application
-------------------


How to run the tests
====================
Dependencies: pytest-2.7.1.tar.gz

Good that you're asking.  The tests are in the
tests/ folder.  
Before to run the tests, start the redis server::

    $ redis-server


To execute the tests *without ACS*, using a mock component::

    $ ./run_coverage

To run the tests *using an ACS component*, the first step is to start ACS and
the ``PositionerContainer``::

    $ source acsconf
    $ acsStart
    $ acsStartContainer -py PositionerContainer

Now it is possible to execute the test with ACS, using the switch ``--acs``::

    $ py.test --acs


Important notes
===============
The Component delegates to ACS comp. That means we always have a name,
also if the component is not alive, and we can raise the same exception
from the mocker and the component, running the tests without ACS installed
or omniorb
