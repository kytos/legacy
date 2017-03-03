Overview
========

The **of.topology** is an app responsible to update links 
between machines and network devices (i.e. switches and 
routers) and them update the current state of the network 
topology. This application depends of another application, 
called **of.lldp**, since it makes use of lldp packets to 
discover links between network devices. 

This application listen for two kinds of packets in. The 
first one is lldp packets which carry information regarding 
the sender, such as port number, mac address, switch id and 
interface. The other packet that this application listen for 
is port status open flow messages. When a packet of this 
kind is received, the application identify which kind of 
change the packet is warning (i.e. created, deleted or 
modified). In both cases, the application returns a Json file 
with all updated changes identified.

Requirements
============

All requirements is installed using the *requirements.txt* packages.

Installing
==========

This is a default Kytos Network Application and the installation process is
straight forward: Just copy the ``kytos/of_topology`` directory to your napps
directory. The default path is ``/var/lib/kytos/napps/``.

.. note:: Please note that you must copy from the root of the napp (including
    the ``kyto`` folder). So you will have
    ``/var/lib/kytos/napps/kytos/of_topology`` at the end.

If you are going to install the whole repository, with all napps, you do not
have to worry about the above procedings, since all napps will be copied into
the correct napps folder during the installation process.

REST API
========

Topology
--------

Using this app the route /kytos/topology will be enable in kyco and will
respond with a json representing network topology.

Network Topology Example
------------------------

A real example of network topology with 3 hosts and 3 switches is
represented below.

.. code:: json

    {
       "nodes":[
          {
             "type":"switch",
             "dpid":"00:00:00:00:00:00:00:02",
             "name":"00:00:00:00:00:00:00:02",
             "serial":"",
             "id":"00:00:00:00:00:00:00:02",
             "software":null,
             "ofp_version":"0x01",
             "connection":"127.0.0.1:49332",
             "data_path":"",
             "manufacturer":"",
             "hardware":""
          },
          {
             "switch":"00:00:00:00:00:00:00:02",
             "type":"interface",
             "port_number":1,
             "name":"s2-eth1",
             "mac":"da:00:35:28:64:d0",
             "id":"00:00:00:00:00:00:00:02:1",
             "speed":"10 Gbps"
          },
          {
             "switch":"00:00:00:00:00:00:00:02",
             "type":"interface",
             "port_number":2,
             "name":"s2-eth2",
             "mac":"76:12:8d:04:43:8f",
             "id":"00:00:00:00:00:00:00:02:2",
             "speed":"10 Gbps"
          },
          {
             "switch":"00:00:00:00:00:00:00:02",
             "type":"interface",
             "port_number":3,
             "name":"s2-eth3",
             "mac":"8a:4d:44:fe:0a:85",
             "id":"00:00:00:00:00:00:00:02:3",
             "speed":"10 Gbps"
          },
          {
             "switch":"00:00:00:00:00:00:00:02",
             "type":"interface",
             "port_number":65534,
             "name":"s2",
             "mac":"e6:35:8d:31:64:46",
             "id":"00:00:00:00:00:00:00:02:65534",
             "speed":""
          },
          {
             "type":"switch",
             "dpid":"00:00:00:00:00:00:00:01",
             "name":"00:00:00:00:00:00:00:01",
             "serial":"",
             "id":"00:00:00:00:00:00:00:01",
             "software":null,
             "ofp_version":"0x01",
             "connection":"127.0.0.1:49328",
             "data_path":"",
             "manufacturer":"",
             "hardware":""
          },
          {
             "switch":"00:00:00:00:00:00:00:01",
             "type":"interface",
             "port_number":1,
             "name":"s1-eth1",
             "mac":"ba:36:c7:2a:f5:6b",
             "id":"00:00:00:00:00:00:00:01:1",
             "speed":"10 Gbps"
          },
          {
             "switch":"00:00:00:00:00:00:00:01",
             "type":"interface",
             "port_number":2,
             "name":"s1-eth2",
             "mac":"36:87:18:7a:19:a5",
             "id":"00:00:00:00:00:00:00:01:2",
             "speed":"10 Gbps"
          },
          {
             "switch":"00:00:00:00:00:00:00:01",
             "type":"interface",
             "port_number":65534,
             "name":"s1",
             "mac":"42:11:03:2c:f5:48",
             "id":"00:00:00:00:00:00:00:01:65534",
             "speed":""
          },
          {
             "type":"switch",
             "dpid":"00:00:00:00:00:00:00:03",
             "name":"00:00:00:00:00:00:00:03",
             "serial":"",
             "id":"00:00:00:00:00:00:00:03",
             "software":null,
             "ofp_version":"0x01",
             "connection":"127.0.0.1:49330",
             "data_path":"",
             "manufacturer":"",
             "hardware":""
          },
          {
             "switch":"00:00:00:00:00:00:00:03",
             "type":"interface",
             "port_number":1,
             "name":"s3-eth1",
             "mac":"e6:60:0a:28:de:a0",
             "id":"00:00:00:00:00:00:00:03:1",
             "speed":"10 Gbps"
          },
          {
             "switch":"00:00:00:00:00:00:00:03",
             "type":"interface",
             "port_number":2,
             "name":"s3-eth2",
             "mac":"06:1d:84:dd:77:0f",
             "id":"00:00:00:00:00:00:00:03:2",
             "speed":"10 Gbps"
          },
          {
             "switch":"00:00:00:00:00:00:00:03",
             "type":"interface",
             "port_number":3,
             "name":"s3-eth3",
             "mac":"62:21:7c:fe:f2:3f",
             "id":"00:00:00:00:00:00:00:03:3",
             "speed":"10 Gbps"
          },
          {
             "switch":"00:00:00:00:00:00:00:03",
             "type":"interface",
             "port_number":65534,
             "name":"s3",
             "mac":"42:f9:63:76:99:43",
             "id":"00:00:00:00:00:00:00:03:65534",
             "speed":""
          }
       ],
       "links":[
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:02",
             "target":"00:00:00:00:00:00:00:02:1"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:02",
             "target":"00:00:00:00:00:00:00:02:2"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:02",
             "target":"00:00:00:00:00:00:00:02:3"
          },
          {
             "type":"link",
             "source":"00:00:00:00:00:00:00:02:3",
             "target":"00:00:00:00:00:00:00:01:1"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:02",
             "target":"00:00:00:00:00:00:00:02:65534"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:01",
             "target":"00:00:00:00:00:00:00:01:1"
          },
          {
             "type":"link",
             "source":"00:00:00:00:00:00:00:01:1",
             "target":"00:00:00:00:00:00:00:02:3"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:01",
             "target":"00:00:00:00:00:00:00:01:2"
          },
          {
             "type":"link",
             "source":"00:00:00:00:00:00:00:01:2",
             "target":"00:00:00:00:00:00:00:03:3"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:01",
             "target":"00:00:00:00:00:00:00:01:65534"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:03",
             "target":"00:00:00:00:00:00:00:03:1"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:03",
             "target":"00:00:00:00:00:00:00:03:2"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:03",
             "target":"00:00:00:00:00:00:00:03:3"
          },
          {
             "type":"link",
             "source":"00:00:00:00:00:00:00:03:3",
             "target":"00:00:00:00:00:00:00:01:2"
          },
          {
             "type":"interface",
             "source":"00:00:00:00:00:00:00:03",
             "target":"00:00:00:00:00:00:00:03:65534"
          }
       ]
    }
