Overview
========

The *of.flow-manager* application exports a REST API to add, remove,
list and clear flows from switches. It can be used by other
applications to manage all flows.

This application creates an abstraction layer to other applications,
since it is only necessary to know the endpoints. The application handles
the requests and return the information already formatted (all endpoints that
receive a ``GET`` return a JSON file).

Installing
==========

All of the Kytos Network Applications are located in the NApps online repository.
To install this NApp, run:

.. code:: shell

   $ kytos napps install kytos/of_flow_manager

If you are going to install kytos-napps from source code, all napps will be
installed by default (just remember you need to enable the ones you want
running).

Advanced
========

Protocol Operation
------------------

The endpoints implemented in this napp are presented in the table below.

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

Examples
--------

For examples on how to use the API and the JSON formats, please refer to EXAMPLES.rst

How it Works
------------

A NApp that wishes to use this application can use http methods, such as
``GET``, ``POST`` and ``DELETE`` to request or send information to it.
All endpoints of this napp return a JSON response as described below.

Endpoint ``/flow-manager/dpid/flows``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a JSON with all flows of a specific switch identified by the DPID.

Endpoint ``/flow-manager/flows``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a JSON with all flows of all switches.

Endpoint ``/flow-manager/dpid/flows-a``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a JSON with success message.

Endpoint ``/flow-manager/dpid/flow_id/flows-d``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Returns a JSON with success message.
