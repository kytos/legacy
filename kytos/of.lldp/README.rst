Overview
========

The *of.lldp* application implements the protocol Link Layer Discovery
Protocol (LLDP). This protocol is vendor free and used to discover
network devices and all links between them. This protocol is implemented
at layer 2 (L2) and defined in the IEEE 802.1ab. A network management
system (NMS) can rapidly obtain the L2 network topology and topology
changes over the time using LLDP.

Advanced
========

Protocol Operation
------------------

LLDP compliant network devices regularly exchange LLDP advertisements
with their neighbors and store it in their internal database (MIB). A
Network Management Software (NMS) can use SNMP to access this
information to build an inventory of the network devices connected on
the network, and for other applications. LLDP advertisements can be sent
to/received from devices that are directly connected with each other
through a physical link.

LLDP have some features it uses in advertising,discovering and learning
neighbor devices. These attributes contain type, length, and value
descriptions and are referred to as TLVs.

TLVs are used by LLDP to receive, send and gather information to and
from their neighbors. Details such as configuration information, device
capabilities, and device identity are information advertised using this
protocol.

Some of common TLVs supported by switches are:

-  Port description TLV;
-  System name TLV;
-  System description TLV;
-  System capabilities TLV;
-  Management address TLV.

It is important to note that some vendors implementes their own TLVs.

How it Works
------------

In order to buid and presents the L2 topology, this application uses the
described protocol. However, in a SDN based network is necessary to
implement the LLDP operation in software.

1. A rule to forward any LLDP packet (ethernet type 0x88cc) to the
   controller is installed in all switches.

2. The switches forward the packet to the controller encapsuled in a
   ``packet_in`` message. The ``packet_in`` contains the original
   message which has the switch datapath id and the port in which the
   LLDP packet was received.

3. The controller sends a LLDP packet to all connected switches and
   stores to which switch and port it was sent.

4. If a different switch forward a LLDP packet sent to another switch,
   the controller knows that both switches are connected.

Example of rule installed in switches to forward LLDP Ethernet packets:

.. code:: bash

    cookie=0x0, duration=779.804s, table=0, n_packets=153, n_bytes=6273,
    idle_age=3, priority=65000,dl_dst=01:23:20:00:00:01,dl_type=0x88cc
    actions=CONTROLLER:65535
