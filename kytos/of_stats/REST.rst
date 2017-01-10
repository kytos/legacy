.. warning:: This document in under construction.

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
