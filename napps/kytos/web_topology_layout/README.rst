Web Topology Layout NApp
========================

This Network App (NApp) manages the settings and layouts of the **Kyco**
web interface (kytos-admin-ui).

It is used to store the interface settings (and layouts) and also to
retrieve this information when requested.

Requirements
============

flask

Installing
==========

This is a default Kytos Network Application and the installation process is
straight forward: Just copy the ``kytos/web_topology_layout`` directory to your
napps directory. The default path is ``/var/lib/kytos/napps/``.

.. note:: Please note that you must copy from the root of the napp (including
    the ``kyto`` folder). So you will have
    ``/var/lib/kytos/napps/kytos/web_topology_layout`` at the end.

If you are going to install the whole repository, with all napps, you do not
have to worry about the above procedings, since all napps will be copied into
the correct napps folder during the installation process.

API
===

The REST endpoints that this NApp exposes are:

-  ``web/topology/layouts``:

   -  This first endpoint only accepts the ``GET`` method and it return
      a list with the name of current available layouts.

-  ``web/topology/layouts/<name>``:

   -  This endpoint accespts both ``GET`` and ``POST`` methods.

      -  The ``GET`` method will return a json with the requested layout
         (), if it exists. Otherwise, it will return a 400 error.
      -  The ``POST`` method receives a json with the data to be saved
         and save it as a json file. These files will be saved at
         ``TOPOLOGY_DIR``, defined on the ``main.py`` file. **For now,
         the default value of this folder is
         ``/tmp/kytos/topologies/``**.

JSON Format
===========

The JSON format format is:

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
