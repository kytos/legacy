########
Overview
########

In order to manage a network, an administrator must have updated and reliable
statistics about the network, in several levels of deepness, since from a
switch port inbound and outbound traffic to the traffic of different connected
networks.

To achieve this, this Network Application collect statistical data provided by
the switches connected to the controller. We *do not use SNMP protocol* because
the OpenFlow protocol already provide these data. The data is stored to be
provided later throught a REST API. This API can supply instant data,
historical data, and also some calculated informations.

The provided statistics, per switch, are the following:

* **Ports**: bytes/sec, utilization, dropped packets/sec and errors/sec split
  into transmission and reception; interface name, MAC address and link speed
  (bps);
* **Flows**: packets/sec, bytes/sec;
* **Description**: manufacturer, hardware, software and datapath descriptions
  and serial number;

############
Requirements
############

Besides Python packages described in *requirements.txt*,
`rrdtool <http://www.rrdtool.org>`__ is required and must be installed by you.

#####
USAGE
#####

*************
Configuration
*************
If you are not satisfied with the link speed provided by the OpenFlow
specification, you can override the switch port speed information by writing
the desired port speed in a file named **user_speed.json** on the root folder
of this NApp. To create it, follow **user_speed.example.json** and the
following notes:

* Speed values are in Gbps;
* Default values:
  * They are optional, but can save a lot of typing;
  * The first *default* will be used when dpid is not found in the file;
  * A *default* value inside a *dpid* will be used for ports that are not specified in that dpid.

There is no need to restart the controller after creating or changing
**user_speed.json**. It is recommended to watch the controller log in case
there is a syntax error

********************
Non-rest interaction
********************

RRD Graphs
==========

If you want to generate graphs using RRD instead of kytos admin web ui, this is
a quick way to do it. This example assumes you are in a subfolder with the
desired ``rrd`` file.

1. First, get the **first** and **last** useful timestamps with:

   .. code:: bash

       rrdtool fetch file.rrd AVERAGE | grep -v nan

2. Optionally, verify the records for the graph:

   .. code:: bash

       rrdtool fetch file.rrd AVERAGE --start [first-1] --end [last-1]

3. Then, make graph subtracting 1 from the first and last useful
   timestamps:

   .. code:: bash

       rrdtool graph speed.png --start [first-1] --end [last-1] \
         DEF:speed=file.rrd:rx_bytes:AVERAGE LINE2:speed#FF0000


REST API
========

As stated on the *Overview* section, this NApp provide some statistics through
a REST API. There are two main groups of statistics provided:

* **Port Statistics**;
* **Flow Statistics**.

All endpoints provided by this NApp are GET Endpoints only, so no POSTs are
allowed. Moreover, the endpoints are all under the url:
*http://<api_url_domain>[:port]/kytos/**stats***.

##########
Developers
##########

If you are going to contribute on the code of this NApp, please remember to run
the test suite prior to do a Pull Request. To run the tests run the following
command:

.. code:: bash

    cd kytos/of.stats
    python -m unittest
