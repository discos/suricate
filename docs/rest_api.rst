***********************
Proposal for DISCOS API
***********************

.. topic:: Preface

   This project aims to build an API for DISCOS clients. The main
   client will be an observer GUI. We want the clients to be able
   to send commands to DISCOS, get the antenna attributes (temperature
   values, positions, etc.), be notified for alarms, get logs, get
   attributes related to the past (i.e. temperature of a receiver
   between datetime x and datetime y, etc.).
   We want to build an HTTP API, in order to make the clients free
   from all ACS constraints (operating system, have ACS installed,
   the programming language to be used, be forced to use no more
   supported programming language, etc.)


Command execution
=================
We want to execute all commands supported by ``Scheduler.cmd()``.
The API endpoint is the following::

    POST /cmd/<cmd-name>

For instance, if we want to execute the command ``getTpi``::

    POST /cmd/getTpi

This call is *non-blocking*. It means that the API executes
``Scheduler.cmd('getTpi')`` in a separate thread, immediately giving back
the control to the client.

The client has to check the status of the command by executing
``GET /cmd/<cmd-name>``, that is::

    GET /cmd/getTpi

The response to this request gives the client a JSON data containing
all information about the command: whether it is still in execution or
terminated, the starting time, the total time of execution, the result in
case it is terminated (in that case the number of TPIs), possible parameters,
errors, etc.

In case a command takes some parameters, they have to be
included in the JSON data sent by the POST request.

It is not possible to have multiple ``Scheduler.cmd('cmd-name')`` in execution at
the same time.  For instance, let's suppose to send a POST request for the ``getTpi`` command and
right after a POST for ``setLO``. If  ``Scheduler.cmd('getTpi')`` is still
in execution, then ``POST /cmd/setLO`` gives an error to the client saying that it is not
possible to execute ``setLO`` because the system is still processing ``getTpi``.

.. note:: This does not mean that you can not execute a command if the
   previous one is running.  For instance, think to ``startScheduler``.
   When you execute it, ``Scheduler.cmd('startScheduler')`` is supposed
   to return immediately. When it returns, it means the execution of ``startScheduler``
   has been processed by the system, and the system is now operating the
   command. As soon as ``Scheduler.cmd('startScheduler')`` returns a
   result, you can execute another command.

In case the client wants to roll back the last command, it has to
send a DELETE request::

   DELETE /cmd

This one will call ``Scheduler.cmd('abort')``.

To get the list of commands from date x to date y::

   GET /cmds/<x>/<y>

To get the list of the last N commands::

   GET /cmds/<N>/

.. note:: It is possible to create new commands, combining some scheduler
   commands.  For instance, if you want to set the proper tpi, you can
   call a custom command that gets the TPIs and set the proper dB values.


.. _antenna_parameters:

How to get antenna parameters
=============================

.. todo:: We read the values from Suricate and push them to the clients
   by using SSE.


Alarms
======

.. todo:: Put the alarm limits in the Suricate configuration file.
   Suricate will check the values and write if there is an alarm.
   The API will read the values from Suricate and push the active
   alarms to the clients by using SSE.


Read values from history
========================

.. todo:: Suricate will save the values to DB. The client
   will perform a GET request specifying the parameters
   of the request: value, starting time, end time, etc.


Logs
====

.. todo:: From :ref:`antenna_parameters` we also get logs about components
   status, containers, ACS.  We need to think about DISCOS logs.
