.. _admin-guide:

***********************************
Suricate System Administrator Guide
***********************************

.. topic:: Preface

   A system administrator in charge of installing, configuring, starting
   and stopping Suricate should read this chapter.


Installation
============
Suricate requires `Redis <https://redis.io/>`_. Additional requirements are
listed in the Suricate's *setup.py* file: we do not care about them because
they will be automatically installed during the Suricate installation.

.. note:: Suricate works with Python 2.7, the same version of the latest
   `ACS <http://www.eso.org/~almamgr/AlmaAcs/index.html>`_ framework.
   Python 2.7 is not supported anymore and maybe at some point we will not be
   able to find the Python 2.7 Suricate dependencies online.  That is why we
   put all of them on a private `DISCOS GitHub repository
   <https://github.com/discos/dependencies/tree/suricate>`_.

Redis
-----
In this section we will see how to install and configure `Redis <https://redis.io/>`_
on Linux CentOS.  If that is not your case, get the source code from the
`Redis website <https://redis.io/download/>`_ and follow the documentation.

On Linux CentOS:

.. code-block:: shell

   sudo yum install redis

To bind Redis server to all ports, open */etc/redis.conf* and
change the line ``bind 127.0.0.1`` to ``bind 0.0.0.0``.
Change also ``protected-mode`` from ``yes`` to ``no``. At this
point:

.. code-block:: shell

   $ sudo chkconfig redis on
   $ sudo service redis restart


Run Suricate from remote
------------------------
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


Suricate
--------
To install Suricate clone the repository and use ``pip``:

.. code-block:: shell

   $ sudo ln -s /alma/ACS-FEB2017/Python/bin/python /bin/python
   $ sudo ln -s /alma/ACS-FEB2017/Python/bin/pip /bin/pip
   $ git clone https://github.com/marco-buttu/suricate.git
   $ cd suricate
   $ sudo pip install .
   $ sudo cp startup/suricate-server /etc/rc.d/init.d/
   $ sudo chkconfig --add suricate-server
   $ sudo chkconfig suricate-server on

At this point Suricate is a startup service.  Before starting we need
to configure it.  To install the SRT configuration:

.. code-block:: bash

   $ suricate-config -t srt

This command copies the SRT configuration to *~/.suricate/config/config.yaml*.
If you want to add or change some antenna parameters, change that file.

Now you are ready to start Suricate:

.. code-block:: shell

   $ sudo service suricate-server start

To know its status and stop it:

.. code-block:: shell

   $ sudo service suricate-server status
   suricate-server is running
   $ sudo service suricate-server stop
   $ sudo service suricate-server status
   suricate-server is NOT running

To uninstall Suricate:

.. code-block:: shell

   $ sudo pip uninstall suricate


Logging
=======
There are three log files you have to take care of:

* *~/.suricate/logs/suricate.log*: user log file, with main information
* *~/.suricate/logs/apscheduler.log*: apscheduler debug file
* */tmp/suricate_service_dbg.log*: service log file
