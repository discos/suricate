.. _admin-guide:

**************************
System Administrator Guide
**************************

.. topic:: Preface

   A system administrator in charge of installing, configuring, starting
   and stopping Suricate should read this chapter.


Installation
============
Suricate requires `Redis <https://redis.io/>`_. Additional requirements are
listed in the Suricate's *setup.py* file: we do not care about them because
they will be automatically installed during the Suricate installation.

.. note:: Suricate works with Python 3.9.4, the same version of the running
   `ACS <http://www.eso.org/~almamgr/AlmaAcs/index.html>`_ framework.

Redis
-----
In this section we will see how to install and configure `Redis <https://redis.io/>`_
on Linux CentOS:

.. code-block:: shell

   $ sudo yum remove redis
   $ wget https://download.redis.io/releases/redis-7.0.15.tar.gz
   $ tar xzf redis-7.0.15.tar.gz
   $ cd redis-7.0.15/
   $ make BUILD_WITH_LTO=no
   $ make test
   $ sudo make install
   $ sudo cp redis.conf /etc
   $ sudo adduser --system --no-create-home redis

Create the file */etc/systemd/system/redis.service* and write the following content::

   [Unit]
   Description=Redis In-Memory Data Store
   After=network.target
   
   [Service]
   ExecStart=/usr/local/bin/redis-server /etc/redis.conf
   ExecStop=/usr/local/bin/redis-cli shutdown
   Restart=always
   User=redis
   Group=redis
   
   [Install]
   WantedBy=multi-user.target

To bind Redis server to all ports, open */etc/redis.conf* and
change the line ``bind 127.0.0.1`` to ``bind 0.0.0.0``.
Change also ``protected-mode`` from ``yes`` to ``no``. At this
point:

.. code-block:: shell

   $ sudo chkconfig redis on
   $ sudo service redis restart

Remote configuration
--------------------
In case Suricate has not been installed on the machine running
the manager, you need to export the manager reference. On the
Suricate machine, open */discos-sw/config/misc/bash_profile* and
write:

.. code-block:: bash

   MNG_IP=192.168.200.203
   export MANAGER_REFERENCE=corbaloc::$MNG_IP:3000/Manager

Upload your public SSH key to the manager host:

.. code-block:: bash

   $ ssh-keygen -t dsa
   $ scp .ssh/id_dsa.pub discos@discos-manager:~

Go to the manager host and add your public SSH key:

.. code-block:: bash

   $ ssh discos@discos-manager
   $ cat id_dsa.pub >> .ssh/authorized_keys
   $ rm id_dsa.pub
   $ logout

Now login to the manager host via SSH and answer ``yes``:

.. code-block:: bash

   $ ssh discos@discos-manager
             ...
   Are you sure you want to continue connecting (yes/no)?

.. note:: In the configuration file need to set the ``RUN_ON_MANAGER_HOST:
   False``. Next section explains how to create a configuration file.

You are now ready to install and use Suricate.


Install Suricate
----------------
To install Suricate, clone the repository as ``discos`` user and use ``pip``:

.. code-block:: shell

   $ git clone https://github.com/discos/suricate.git
   $ cd suricate
   $ pip install .
   $ sudo cp startup/suricate.service /lib/systemd/system/
   $ sudo systemctl daemon-reload

At this point Suricate can be executed as a service.  Before starting we need
to configure it.  There are three configuration available: ``srt``, ``medicina``
and ``noto``. For instance, if you want to load the SRT configuration, give it as a template
argument:

.. code-block:: bash

   $ suricate-config -t srt

This command copies the SRT configuration to *~/.suricate/config/config.yaml*.
If you want to add or change some antenna parameters, change that file.


Create the database
-------------------

.. todo:: All these steps must be deployed automatically. To be done.

Create the database tables::

   $ cd suricate/suricate
   $ source .flaskenv
   $ flask db init

Every time a table changes::

   $ flask db migrate -m "Task table"
   $ flask db upgrade


Run Suricate
------------

If you want to send the commands to DISCOS, start the redis queue::

   $ rqworker -P ~/suricate/suricate discos-api


Now you are ready to start Suricate:

.. code-block:: shell

   $ sudo service suricate start

If you want to know the status of Suricate:

.. code-block:: shell

   $ sudo service suricate status
   [...]
      Active: active (running) since [...]
   [...]
   $ sudo systemctl stop suricate.service
   $ sudo systemctl status suricate.service
   [...]
      Active: inactive (dead)
   [...]

If you want to stop it:

.. code-block:: shell

   $ sudo service suricate stop

To uninstall Suricate:

.. code-block:: shell

   $ sudo pip uninstall suricate


Logging
=======
There are two log files you have to take care of:

* *~/.suricate/logs/suricate.log*: user log file, with main information
* *~/.suricate/logs/apscheduler.log*: apscheduler debug file

along with the service output:

.. code-block:: shell

   $ sudo systemctl status suricate.service
   [...]
   Apr 04 14:12:20 manager.development.inaf.it bash[1910]: 04-Apr-24 14:12:20 | INFO | OK - component ANTENNA/Boss is online
   Apr 04 14:12:20 manager.development.inaf.it bash[1910]: 04-Apr-24 14:12:20 | INFO | OK - component ANTENNA/Boss is online
   Apr 04 14:12:21 manager.development.inaf.it bash[1910]: 04-Apr-24 14:12:21 | INFO | OK - component ANTENNA/Boss is online
   Apr 04 14:12:21 manager.development.inaf.it bash[1910]: 04-Apr-24 14:12:21 | INFO | OK - component ANTENNA/Boss is online
   [...]
