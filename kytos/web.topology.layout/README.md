Requirements
============

API
===
The base url is `/web.topology.layout/`. A GET on this URL will return the
name of the stored topologies. A POST, that must contain a JSON with a valid
topology, will save this topology.

The url '/web.topology.layout/<topology_name>' will return the json of the
stored topology.

Tests
=====

