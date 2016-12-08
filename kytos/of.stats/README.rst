Overview
========

The *of.stats* application collects, stores and provides statistics
about the following data per switch:

  * **Ports**: bytes/sec, utilization, dropped packets/sec and errors/sec split into transmission and reception; interface name, MAC address and link speed (bps);
  * **Flows**: packets/sec, bytes/sec;
  * **Description**: manufacturer, hardware, software and datapath descriptions and serial number;

Requirements
------------

Besides Python packages in *requirements.txt*,
`rrdtool <http://www.rrdtool.org>`__ is required.

REST API
========

Port Statistics
---------------

-  **/kytos/stats/[*dpid*]/ports**: List all ports of the switch
   identified by *dpid* and the latest number for each statistic type.
   Also provide the interface name, MAC address and link speed (bps);
-  **/kytos/stats/[*dpid*]/ports/[*port*]**: Provide more numbers
   (latest ones) for each statistic type for port *port* of switch
   *dpid*;
-  **/kytos/stats/[*dpid*]/ports/[*port*]?start=[*start*]&end=[*end*]**:
   Provide statistics between *start* and *end* (UNIX timestamps). If
   **start=[*start*]&** is omitted, use the oldest entry as *start*. If
   **&end=[*end*]** is omitted, use the time of the request as *end*.

Flow Statistics
---------------

-  **/kytos/stats/[*dpid*]/flows**: List all flows of the switch
   identified by *dpid*, their IDs and the latest number for each
   statistic type;
-  **/kytos/stats/[*dpid*]/flows/[*ID*]**: Provide more numbers (latest
   ones) for each statistic for flow *ID* of switch *dpid*.
-  **/kytos/stats/[*dpid*]/flows/[*ID*]?start=[*start*]&end=[*end*]**:
   Provide statistics between *start* and *end* (UNIX timestamps). If
   **start=[*start*]&** is omitted, use the oldest entry as *start*. If
   **&end=[*end*]** is omitted, use the time of the request as *end*.

Advanced
========

Overriding Link Speed
---------------------

If you are not satisfied with the link speed provided by the OpenFlow
specification, you can set the exact speed of your links in the file
``user_speed.json``. To create it, follow ``user_speed.example.json``
and the following notes: \* Speed values are in Gbps; \* Default values:
\* They are optional, but can save a lot of typing; \* The first
*default* will be used when *dpid* is not found in the file; \* A
*default* value inside a *dpid* will be used for ports that are not
specified in that *dpid*.

There is no need to restart the controller after creating or changing
``user_speed.json``. It is recommended to watch the controller log in
case there is a syntax problem.

Developers
----------

To run tests:

.. code:: bash

    cd kytos/of.stats
    python -m unittest

RRD Graphs
----------

If you want to generate graphs using RRD instead of kytos admin web ui,
this is a quick way to do it. This example assumes you are in a
subfolder with the desired ``rrd`` file.

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
