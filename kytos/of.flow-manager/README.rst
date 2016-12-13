Overview
========

The *of.flow-manager* application exports a REST API to add, remove,
list and clean flows from switches. It can be used by others
applications to manage all flows.

This applications creates an abstraction layer to other applications,
since it is only necessary to know only the endpoints. The application
takes care to handle the requests and return the information already
formatted (all endpoints that receive a ``GET`` returns an JSON file).

Advanced
========

Protocol Operation
------------------

The endpoints implemented by this napp is presented in table below.

+----------------------------------------+----------------------------------+------------+
| Endpoint                               | Description                      | Method     |
+========================================+==================================+============+
| ``/flow-manager/dpid/flows``           | Retrieve flows from a specific   | ``GET``    |
|                                        | Switch                           |            |
+----------------------------------------+----------------------------------+------------+
| ``/flow-manager/flows``                | Retrieve all flows               | ``GET``    |
+----------------------------------------+----------------------------------+------------+
| ``/flow-manager/dpid/flows-a``         | Add a flow in a specific Switch  | ``POST``   |
|                                        |                                  |            |
+----------------------------------------+----------------------------------+------------+
| ``/flow-manager/dpid/flow_id/flows-d`` | Delete a flow from a specific    | ``DELETE`` |
|                                        | Switch                           |            |
+----------------------------------------+----------------------------------+------------+

How it Works
------------

An application that wishes to use this application, can use http
methods, such as ``GET``,\ ``POST`` and ``DELETE`` to request or send an
information to the napp. All endpoints of this napp returns a JSON
response as described below.

Endpoint ``/flow-manager/dpid/flows``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a JSON with all flows of a specific switch identified by the
DPID.

Endpoint ``/flow-manager/flows``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a JSON with all flows of all switches.

Endpoint ``/flow-manager/dpid/flows-a``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a JSON with success message.

Endpoint ``/flow-manager/dpid/flow_id/flows-d``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a JSON with success message.
