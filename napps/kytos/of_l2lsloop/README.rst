Overview
========

The *of.l2lsloop* application is used to avoid loops at Layer 2. A loop
at layer 2 occurs when there is more than one path between two endpoints
(e.g. multiple connections between two network switches or two ports on
the same switch connected to each other).

A loop can create broadcast storms when broadcast or unicast messages
are forwarded by switches in every port. These messages can be
replicated indefinitely by network switches, causing the broadcast
storm. Since the layer 2 header does not support a time to live (TTL)
value, if a frame is sent to a looped topology, it can loop forever.

It is important to cite that this application **is not** working yet.

Installing
==========

All the Kytos Network Applications are located in the NApps online repository.
To install this NApp, run:

.. code:: shell

   $ kytos napps install kytos/of_l2lsloop

If you are going to install kytos-napps from source code, all napps will be
installed by default (just remember you need to enable the ones you want
running).

Advanced
========

L2LSLOOP Operation
------------------

In order to avoid loop at Layer 2, this application identifies duplicate
paths between endpoints and remove one of the paths by disabling one of
the ports that are creating the loop.
