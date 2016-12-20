Overview
========

The *of.l2ls* application is used in basic operations of switches. It
implements the algorithm know as L2 Learning Switch, which aims to
figure out which host is attached to which port. So, when a frame is
addressed to a host, it is forwarded directly to the correct port. Note
that, without this application, the switch would acts just as hub,
broadcasting all frames to all ports.

Installing
==========

This is a default Kytos Network Application and the installation process is
straight forward: Just copy the ``kytos/of.l2ls`` directory to your napps
directory. The default path is ``/var/lib/kytos/napps/``.

.. note:: Please note that you must copy from the root of the napp (including
    the ``kyto`` folder). So you will have
    ``/var/lib/kytos/napps/kytos/of.l2ls`` at the end.

If you are going to install the whole repository, with all napps, you do not
have to worry about the above procedings, since all napps will be copied into
the correct napps folder during the installation process.

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
