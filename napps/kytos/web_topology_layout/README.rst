Web Topology Layout NApp
========================

This Network App (NApp) manages the settings and layouts of the **Kytos**
web interface (kytos-admin-ui).

It is used to store the interface settings (and layouts) and also to
retrieve this information when requested.

Requirements
============

flask

Installing
==========

All of the Kytos Network Applications are located in the NApps online repository.
To install this NApp, run:

.. code:: shell

   $ kytos napps install kytos/web_topology_layout

If you are going to install kytos-napps from source code, all napps will be
installed by default (just remember you need to enable the ones you want
running).

API
===

The REST endpoints this NApp exposes are:

-  ``web/topology/layouts``:

   -  This first endpoint only accepts the ``GET`` method and it returns
      a list with the name of current available layouts.

-  ``web/topology/layouts/<name>``:

   -  This endpoint accepts both ``GET`` and ``POST`` methods.

      -  The ``GET`` method will return a JSON with the requested layout(),
         if it exists. Otherwise, it will return a 400 error.
      -  The ``POST`` method receives a JSON with the data to be saved
         and save it as a file. These files will be saved at
         ``TOPOLOGY_DIR``, defined on the ``main.py`` file. **For now,
         the default value of this folder is
         ``/tmp/kytos/topologies/``**.

JSON Format
===========

The JSON format is:

.. code:: json

    {
      "other_settings": {
        "show_topology": <boolean>,
        "map_zoom": <integer>,
        "show_unused_interfaces": <boolean>,
        "show_disconnected_hosts": <boolean>,
        "topology_transformation": <transformation>,
        "show_map": <boolean>,
        "map_center": {
          "lng": <decimal>,
          "lat": <decimal>
        }
      },
      "nodes": {
        <node_id>: {
          "id": <node_id>,
          "name": <node_name>,
          "x": <x_position>,
          "y": <y_position>,
          "fx": <fx_position>,
          "fy": <fy_position>,
          "downlight": <boolean>,
          "type": <node_type>
        },
        <node_id>: {
          "id": <node_id>,
          "name": <node_name>,
          "x": <x_position>,
          "y": <y_position>,
          "fx": <fx_position>,
          "fy": <fy_position>,
          "downlight": <boolean>,
          "type": <node_type>
        }.
        ...
      }
    }

-  other settings:

   -  : string - "translate(, ) scale()",

      -  : decimal
      -  : decimal
      -  : decimal

-  nodes:

   -  : string
   -  : string
   -  : decimal
   -  : decimal
   -  : decimal (or null if not fixed position)
   -  : decimal (or null if not fixed position)
   -  : string ("switch" \| "host" \| "interface")
