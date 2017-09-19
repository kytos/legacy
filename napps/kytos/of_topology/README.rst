Overview
========

The **of.topology** is a NApp responsible to update links
between machines and network devices (i.e. switches and
routers) and then update the current state of the network
topology. This application depends of another application,
**of.lldp**, since it makes use of lldp packets to
discover links between network devices.

This application listens for two kinds of packet_in events. The
first one is lldp packets which carry information regarding
the sender, such as port number, mac address, switch id and
interface. The other packet that this application listens for
is port status open flow messages. When a packet of this
kind is received, the application identifies which kind of
change the packet is warning about (i.e. created, deleted or
modified). In both cases, the application returns a Json file
with all updated changes identified.

Requirements
============

All requirements are listed in *requirements.txt*.

Installing
==========

All of the Kytos Network Applications are located in the NApps online repository.
To install this NApp, run:

.. code:: shell

   $ kytos napps install kytos/of_topology

If you are going to install kytos-napps from source code, all napps will be
installed by default (just remember you need to enable the ones you want
running).

REST API
========

For information about this NApp's endpoints, please refer to the 'Rest API' tab in its `NApps Server page <https://napps.kytos.io/kytos/of_topology>`_.
