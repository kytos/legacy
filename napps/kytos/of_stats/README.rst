Overview
========

In order to manage a network, an administrator must have updated and reliable
statistics about it, in several levels of deepness, from a
switch port inbound and outbound traffic to the traffic of different connected
networks.

To achieve that, this Network Application collects statistical data provided by
the switches connected to the controller. We *do not use SNMP protocol* because
the OpenFlow protocol already provide this data. The data is stored to be
provided later through a REST API. This API can supply instant data,
historical data, and also some calculated information.

The provided statistics, per switch, are:

* **Ports/Interfaces**: bytes/sec, utilization, dropped packets/sec and
  errors/sec split into transmission and reception; interface name, MAC address
  and link speed (bps);
* **Flows**: packets/sec, bytes/sec;

Requirements
============

Besides Python packages described in *requirements.txt*,
`rrdtool <http://www.rrdtool.org>`__ is required and must be installed. If you
are using Ubuntu, you must install, using apt:

.. code-block:: shell

   apt install rrdtool python3.6-dev librrd-dev

.. note:: We currently use rrd to keep persistence in data, but future
    versions of this napp will allow you to choose what kind of backend you
    want to use.

Installing
==========

All of the Kytos Network Applications are located in the NApps online repository.
To install this NApp, run:

.. code:: shell

   $ kytos napps install kytos/of_stats

If you are going to install kytos-napps from source code, all napps will be
installed by default (just remember you need to enable the ones you want
running).

REST API
--------

As stated on the *Overview* section, this NApp provides some statistics through
a REST API. There are two main groups of statistics provided:

* **Port Statistics**;
* **Flow Statistics**.

All endpoints provided by this NApp are GET Endpoints only, so no POSTs are
allowed. For more information about the REST API please visit the file
``REST.rst``.

Troubleshooting
===============

.. attention:: The filenames below are relative to this NApp's folder.
   If you run Kytos as root, it is ``/var/lib/kytos/napps/kytos/of_stats`` or,
   if using virtualenv, ``$VIRTUAL_ENV/var/lib/kytos/napps/kytos/of_stats``.

Wrong link utilization
----------------------
Sometimes, the link speed is wrongly reported by the switch or there's no such
speed specified in the protocol. In these cases, you can manually define the
speeds in the file ``user_speed.json``. Changes to this file will be loaded
automatically without the need to restart the controller.

Setting the interface speeds manually is quite easy. Create ``user_speed.json``
following the provided ``user_speed.example.json`` file. Let's see what the
example means:

.. code-block:: json

   {
     "default": 100,
     "00:00:00:00:00:00:00:01":
     {
       "default": 10,
       "4": 1
     }
   }

The speed is specified in Gbps (not necessarily integers). The first line has
an optional *default* value that specify the speed of any interface that is not
found in this file. The switch whose dpid is *00:...:00:01* also has an
optional *default* value of 10 Gbps for all its ports except the number 4 that
is 1 Gbps. If there is no *default* value and the dpid or port is not
specified, the speed will be taken following the OpenFlow specifications.
To make it clear, find below the speed of some interfaces when
``user_speed.json`` has the content above:

+-------------------------+------+--------------+
|          DPID 1         | Port | Speed (Gbps) |
+=========================+======+==============+
| 00:00:00:00:00:00:00:01 |  4   |        1     |
+-------------------------+------+--------------+
| 00:00:00:00:00:00:00:01 |  2   |       10     |
+-------------------------+------+--------------+
| 00:00:00:00:00:00:00:02 |  4   |      100     |
+-------------------------+------+--------------+
| 00:00:00:00:00:00:00:02 |  2   |      100     |
+-------------------------+------+--------------+

Changing settings.py (advanced)
-------------------------------
Some changes in ``settings.py`` require recreating the database. Check the
section ``Deleting the database`` above.

Deleting the database
---------------------
You don't have to stop the controller to delete the databases. This NApp will
recreate them as needed after you run:

.. code-block:: shell

   rm -rf rrd/flows rrd/ports

