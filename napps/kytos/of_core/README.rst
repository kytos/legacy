Overview
========

The NApp **of.core** is a NApp responsible to handle OpenFlow basic
operations. The messages covered are:

-  hello messages;
-  reply echo request messages;
-  request stats messages;
-  send a feature request after echo reply;
-  update flow list of each switch;
-  update features;
-  handle all input messages;

Requirements
============

All requirements are listed in *requirements.txt*.

Installing
==========

All of the Kytos Network Applications are located in the NApps online
repository. To install this NApp, run:

.. code:: shell

   $ kytos napps install kytos/of_core

If you are going to install kytos-napps from source code, all napps will be
installed by default (just remember you need to enable the ones you want
running).
