.. _dev-guide:

*****************
Development Guide
*****************

Architecture
============

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
