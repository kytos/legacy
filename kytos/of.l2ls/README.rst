Overview
========

The *of.l2ls* application is used in basic operations of switches. It
implements the algorithm know as L2 Learning Switch, which aims to
figure out which host is attached to which port. So, when a frame is
addressed to a host, it is forwarded directly to the correct port. Note
that, without this application, the switch would acts just as hub,
broadcasting all frames to all ports.

Advanced
========

L2 Learning Switch Operation
----------------------------

At the switch startup, it does not know which hosts are attached to
which port. So, when a host A sends a frame, addressed to host B, the
switch will broadcast this frame to all ports, except to the port which
the frame has arrived. At same time, the switch learns which port the
host A is attached. A table is stored in switch's local memory mapping
the host mac address and port number.

When the host B answers the request, the switch adds to this table an
entry mapping the mac address of host B to the port in which it is
connected. This process goes on until the switch learns which port all
hosts are connected.
