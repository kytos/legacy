.. warning:: This document in under construction.

REST API
========

Port Statistics
---------------

 -  **/api/legacy/of_stats/[*dpid*]/ports**: List all ports of the switch
    identified by *dpid* and the latest number for each statistic type.
    Also provide the interface name, MAC address and link speed (bps);

 -  **/api/legacy/of_stats/[*dpid*]/ports/[*port*]**: Provide more numbers
    (latest ones) for each statistic type for port *port* of switch
    *dpid*;

 -  **/api/legacy/of_stats/[*dpid*]/ports/[*port*]?start=[*start*]&end=[*end*]**:
    Provide statistics between *start* and *end* (UNIX timestamps). If
    **start=[*start*]&** is omitted, use the entire database period. If
    **&end=[*end*]** is omitted, use the time of the request as *end*.

Flow Statistics
---------------

 -  **/api/legacy/of_stats/[*dpid*]/flows**: List all flows of the switch
    identified by *dpid*, their IDs and the latest number for each statistic
    type;

 -  **/api/legacy/of_stats/[*dpid*]/flows/[*ID*]**: Provide more numbers
    (latest ones) for each statistic for flow *ID* of switch *dpid*.

 -  **/api/legacy/of_stats/[*dpid*]/flows/[*ID*]?start=[*start*]&end=[*end*]**:
    Provide statistics between *start* and *end* (UNIX timestamps). If
    **start=[*start*]&** is omitted, use the entire database period. If
    **&end=[*end*]** is omitted, use the time of the request as *end*.

Troubleshooting
---------------

I get only zeros
................
Try specifying the start parameter.

Wrong link utilization
......................
Sometimes, the link speed is not correctly informed by the switch. Check the
section with the same name in ``README.rst``.

Other issues
............
Try deleting the database as described in ``README.rst``.
