.. _admin-guide:

**************************
System Administrator Guide
**************************

.. topic:: Preface

   This chapter explains how to install and configure Suricate
   on a virtual machine where provisioning for DISCOS has already
   been completed. This part is intended for system administrators.


The Virtual Machine
===================
Download `this virtual machine
<https://drive.google.com/file/d/1x1EbixIGrj1qFmQIkdv8wVTj7-Emnd2b/view?usp=drive_link>`_, where provisioning for DISCOS has already been completed.
After that, import the VM using VirtualBox, leaving the default options
unchanged, then start it.


Deployment
==========
Log into the virtual machine::

   $ ssh -X discos@192.168.56.200

Clone Suricate and run the automatic deployment::

   $ git clone https://github.com/discos/suricate.git
   $ cd suricate
   $ ./deploy.sh  # Password for discos user is requested

At the end of the deployment, the virtual machine is automatically
restarted.


Check the status
================
Once the virtual machine is restarted, login::

   $ ssh -X discos@192.168.56.200

Verify the status of Suricate. The output should indicate
``Active: active (running)``::

   $ service suricate status
   Redirecting to /bin/systemctl status suricate.service
   ● suricate.service - DISCOS monitoring program
   Loaded: loaded (/etc/systemd/system/suricate.service; ...)
   Active: active (running) sice ...
       ...

Redis has to be active as well::

   $ service redis status
       ...
   Active: active (running) since ...
       ...

To stop and start Suricate::

   $ sudo service suricate stop  # Stop suricate service
   $ sudo service suricate start # Start suricate service


Remote ACS manager
==================
If the ACS manager is not running on the virtual machine but on a
remote machine instead, then you need to export the manager reference.
On the virtual machine open */discos-sw/config/misc/bash_profile*,
write the manager IP and export the manager reference, as indicated
below (for an ACS manager running on ``192.168.200.203``):

.. code-block:: bash

   # That's the file /discos-sw/config/misc/bash_profile
   MNG_IP=192.168.200.203
   export MANAGER_REFERENCE=corbaloc::$MNG_IP:3000/Manager

Upload your public SSH key to the manager host:

.. code-block:: bash

   $ ssh-keygen -t dsa
   $ scp .ssh/id_dsa.pub discos@192.168.200.203:~

Go to the manager host and add your public SSH key:

.. code-block:: bash

   $ ssh discos@192.168.200.203
   $ cat id_dsa.pub >> .ssh/authorized_keys
   $ rm id_dsa.pub
   $ logout

Now login to the manager host via SSH and answer ``yes``:

.. code-block:: bash

   $ ssh discos@192.168.200.203
             ...
   Are you sure you want to continue connecting (yes/no)?

Open the file *~/.suricate/config/config.yaml*, in the last line
set ``RUN_ON_MANAGER_HOST`` to ``False``.


Logging
=======
There are two log files you should pay attention to:

* *~/.suricate/logs/suricate.log*: that's the user log file;
* *~/.suricate/logs/apscheduler.log*: debug logfile of Python
  *apscheduler* library.
