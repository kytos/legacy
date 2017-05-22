Overview
========

This file contains examples on how to communicate with the REST API of the
Flow Manager NApp.

Please note all JSON strings in this file are formatted for better
visualization.

Retrieving flows from switches
==============================

Examples:
---------

Requesting flows from all the switches in the topology:

.. code:: shell

  curl -X GET 127.0.0.1:8181/kytos/flow-manager/flows

Requesting flows from a specific switch:

.. code:: shell

  curl -X GET 127.0.0.1:8181/kytos/flow-manager/flows/00:00:00:00:00:00:00:01

Output JSON format
------------------

The output JSON will have a dictionary with *dpid* as key and a *list of flows*
as a value. Each switch will have it's own key. Each flow in the list is
represented as a dictionary as seen below.

.. code:: json

  {
    "00:00:00:00:00:00:00:01": {
      "e972d1a60d34c249afa6aa929cb6c5a6": {
        "idle_timeout": 0,
        "hard_timeout": 0,
        "priority": 0,
        "table_id": 0,
        "buffer_id": null,
        "in_port": 0,
        "dl_src": "ee:74:70:5c:05:42",
        "dl_dst": "a6:e8:20:f5:3e:32",
        "dl_vlan": 0,
        "dl_type": 2054,
        "nw_src": "0.0.0.0",
        "nw_dst": "0.0.0.0",
        "tp_src": 0,
        "tp_dst": 0,
        "actions": [
          {
            "type": "action_output",
            "port": 1
          }
        ]
      },
      "c096bfc0be1c7313015fa9b35ae10f15": {
        "idle_timeout": 0,
        "hard_timeout": 0,
        "priority": 0,
        "table_id": 0,
        "buffer_id": null,
        "in_port": 0,
        "dl_src": "a6:e8:20:f5:3e:32",
        "dl_dst": "ee:74:70:5c:05:42",
        "dl_vlan": 0,
        "dl_type": 2048,
        "nw_src": "0.0.0.0",
        "nw_dst": "0.0.0.0",
        "tp_src": 0,
        "tp_dst": 0,
        "actions": [
          {
            "type": "action_output",
            "port": 2
          }
        ]
      } 
    },
    "00:00:00:00:00:00:00:02": {
      "45a0dee7ffcca5b39c826b97998a2c25": {
         "idle_timeout": 0,
         "hard_timeout": 0,
         "priority": 0,
         "table_id": 0,
         "buffer_id": null,
         "in_port": 0,
         "dl_src": "ee:74:70:5c:05:42",
         "dl_dst": "a6:e8:20:f5:3e:32",
         "dl_vlan": 0,
         "dl_type": 2054,
         "nw_src": "0.0.0.0",
         "nw_dst": "0.0.0.0",
         "tp_src": 0,
         "tp_dst": 0,
         "actions": [
           {
             "type": "action_output",
             "port": 2
           }
         ]
       },
      "36918a1b822646912903de6b399b3717": {
        "idle_timeout": 0,
        "hard_timeout": 0,
        "priority": 0,
        "table_id": 0,
        "buffer_id": null,
        "in_port": 0,
        "dl_src": "a6:e8:20:f5:3e:32",
        "dl_dst": "ee:74:70:5c:05:42",
        "dl_vlan": 0,
        "dl_type": 2048,
        "nw_src": "0.0.0.0",
        "nw_dst": "0.0.0.0",
        "tp_src": 0,
        "tp_dst": 0,
        "actions": [
          {
            "type": "action_output",
            "port": 1
          }
        ]
      }
    }
  }

Inserting new flows in switches
===============================

Examples
--------

To insert flows in a switch one needs to send a JSON file with the Input format
below to the API endpoint, using the POST method.

Inserting a flow in all switches in the topology:

.. code:: shell

  curl -X POST -H "Content-Type: application/json" -d '<list of flows>' 127.0.0.1:8181/kytos/flow-manager/flows/

Inserting a flow in a specific switch:

.. code:: shell

  curl -X POST -H "Content-Type: application/json" -d '<list of flows>' 127.0.0.1:8181/kytos/flow-manager/flows/00:00:00:00:00:00:00:01


Input JSON format
-----------------

The input JSON must be a list of flow dictionaries (even if there is a single
flow). Wildcarded fields can be omitted.

For instance, if one needs flows to block a specific source mac_address
(say 00:15:af:d5:38:98) and send all ipv6 traffic to the controller, the JSON
string should be:

.. code:: json

  [
    {
      "dl_src": "00:15:af:d5:38:98"
    },
    {
      "dl_type": 34525,
      "actions": [
        {
          "type": "action_output",
          "port": 65533
        }
      ]
    }
  ]

Removing existing flows from switches
=====================================

Examples
--------

To delete flows from a switch one needs to send a request using the DELETE
method to the API endpoint. The URL contains the switch dpid and the *flow_id*,
which may be obtained using the *retrieve* endpoint. Omitting the flow_id
will remove all available flows.

Removing the very first flow presented in this file:

.. code:: shell

  curl -X DELETE 127.0.0.1:8181/kytos/flow-manager/flows/00:00:00:00:00:00:00:01/e972d1a60d34c249afa6aa929cb6c5a6

Removing all flows from a specific switch:

.. code:: shell

  curl -X DELETE 127.0.0.1:8181/kytos/flow-manager/flows/00:00:00:00:00:00:00:01

Removing all flows from all switches in the topology:

.. code:: shell

  curl -X DELETE 127.0.0.1:8181/kytos/flow-manager/flows

