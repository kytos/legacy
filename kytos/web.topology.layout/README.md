Web Topology Layout NApp
========================

This Network App (NApp) manages the settings and layouts of the **Kyco** web
interface (kytos-admin-ui).

It is used to store the interface settings (and layouts) and also to retrieve
this information when requested.

Requirements
============
flask

API
===
The REST endpoints that this NApp exposes are:

- `web/topology/layouts`:
    - This first endpoint only accepts the `GET` method and it return a list
    with the name of current available layouts.
- `web/topology/layouts/<name>`:
    - This endpoint accespts both `GET` and `POST` methods.
        - The `GET` method will return a json with the requested layout
        (<name>), if it exists. Otherwise, it will return a 400 error.
        - The `POST` method receives a json with the data to be saved and save
        it as a json file. These files will be saved at `TOPOLOGY_DIR`, defined
        on the `main.py` file. **For now, the default value of this folder is
        `/tmp/kytos/topologies/`**.

JSON Format
===========
The JSON format format is:

```json
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
```

- other settings:
    - <transformation>: string - "translate(<x_translation>, <y_translation>) scale(<scale>)",
        - <x_translation>: decimal
        - <y_translation>: decimal
        - <scale>: decimal
- nodes:
    - <node_id>: string
    - <node_name>: string
    - <x_position>: decimal
    - <y_position>: decimal
    - <fx_position>: decimal (or null if not fixed position)
    - <fy_position>: decimal (or null if not fixed position)
    - <node_type>: string ("switch" | "host" | "interface")
    
