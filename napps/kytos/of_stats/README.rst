Overview
========

In order to manage a network, an administrator must have updated and reliable
statistics about the network, in several levels of deepness, since from a
switch port inbound and outbound traffic to the traffic of different connected
networks.

To achieve that, this Network Application collect statistical data provided by
the switches connected to the controller. We *do not use SNMP protocol* because
the OpenFlow protocol already provide these data. The data is stored to be
provided later through a REST API. This API can supply instant data,
historical data, and also some calculated information.

The provided statistics, per switch, are the following:

* **Ports/Interfaces**: bytes/sec, utilization, dropped packets/sec and
  errors/sec split into transmission and reception; interface name, MAC address
  and link speed (bps);
* **Flows**: packets/sec, bytes/sec;

Requirements
============

Besides Python packages described in *requirements.txt*,
`rrdtool <http://www.rrdtool.org>`__ is required and must be installed by you.

.. note:: Today, we are using rrd to persist this data. But in fact future
    versions of this napp will allow you to choose what kind of backend you
    want to use.

Installing
==========

This is a default Kytos Network Application and the installation process is
straight forward: Just copy the ``kytos/of_stats`` directory to your napps
directory. The default path is ``/var/lib/kytos/napps/``.

.. note:: Please note that you must copy from the root of the napp (including
    the ``kyto`` folder). So you will have
    ``/var/lib/kytos/napps/kytos/of_stats`` at the end.

If you are going to install the whole repository, with all napps, you do not
have to worry about the above procedings, since all napps will be copied into
the correct napps folder during the installation process.

REST API
--------

As stated on the *Overview* section, this NApp provide some statistics through
a REST API. There are two main groups of statistics provided:

* **Port Statistics**;
* **Flow Statistics**.

All endpoints provided by this NApp are GET Endpoints only, so no POSTs are
allowed. For more information about the REST API please visit the file
``REST.rst``.
