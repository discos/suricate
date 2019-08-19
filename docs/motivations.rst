.. _motivations:

Motivations
===========
ACS has already a `property sampling system
<http://www.eso.org/~almamgr/AlmaAcs/OnlineDocs/ACS_Sampling_System.pdf>`_,
so why do we need Suricate? Here are some reasons:

* in order for a client to ask for the property values, it must have ACS
  properly configured and running. This means the clients have to install
  ACS, and understand how ACS works from a really poor and outdated
  documentation. In addition, they need to use a particular operating
  system and follow a very long list of requirements: particular version
  of libraries, programming languages, and so forth.
  The Suricate clients are independent from ACS, from the operating system and
  also from the programming language (there are about 50 programming languages
  supported);
* the ACS documentation says that the ACS sampling system supports only four
  property types (``ROdouble``, ``RWdouble``, ``ROlong`` and ``RWlong``),
  and no sequences, while Suricate supports every type of property and also
  property sequences;
* the ACS sampling system has no error handling inside the sampling thread;
  this means that if some sampled values are lost or there is a notification
  channel failure, this will not be notified to the user. This means in case
  of failures, the user will not know what is appening to the system;
* the ACS system gets only the properties values, while Suricate is able to
  collect also the component methods outupt;
* ACS is poorly documented, and it is really hard to understand what happens
  under the hood.
