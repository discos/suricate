.. _api:

*********************************
Application Programming Interface
*********************************

This chapter explains how to send commands to the control system
and how to get the antenna parameters by means of an HTTP API.
You can build your clients in whatever programming language you
want and make it running on any operating system.


How to get the antenna parameters
=================================
The :download:`SRT configuration file <../templates/srt.yaml>` contains all
parameters you can get. Have a look at its first 20 lines:

.. literalinclude:: ../templates/srt.yaml
   :language: yaml
   :lines: 1-20
   :linenos:

Basically there is a list of *components*, and every component
has some parameters (*properties* or *methods*) that you can ask for.
They are identified by the lable ``name``, it means, regarding to previous
lines, you can get the following ``ANTENNA/Boss`` parameters: ``rawAzimuth``,
``rawElevation``, ``observedAzimuth``, ``observedElevation``.

Let's see how to get them by using a Python client.


How to execute a command
========================


How to get the command status
=============================


