########################
Suricate's documentation
########################

.. topic:: Preface

   GUIs, RFI checkers, receiver monitors, backends, meteo services,
   they all need to know some antenna parameters like the current
   azimuth and elevation, device temperatures, configurations, LO
   frequencies and so forth. This documentation shows how to
   easily get them by means of an application called Suricate,
   composted by three packages: :ref:`api`, :ref:`monitor`,
   and :ref:`alarms`. There is one chapter for each package and
   the first one, :ref:`api`, explains how to use the HTTP API to
   send commands to the control system and to get all antenna parameters.
   If you are a system administrator in charge of installing Suricate,
   please read the :ref:`admin-guide`.



Contents
========

.. toctree::
   :maxdepth: 1

   api.rst
   monitor.rst
   alarms.rst
   adminguide.rst
