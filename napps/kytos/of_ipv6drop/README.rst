Overview
========

The *of.ipv6drop* network application (NApp) install a flow on the
connected switches so that they *DROP* all ipv6 incoming packets. Once
the NApp is loaded on the controller it work by itself, without the need
of any user interaction.

To do so, the NApp listen to all ``kytos/core.switches.new`` events (that
represents a new switch connected) and send to this switch a FlowMod
message to install the DROP IPv6 flow (match ``dl_type`` == ``0x86dd``).

Requirements
============

All requirements is installed using the *requirements.txt* packages.

Installing
==========

All the Kytos Network Applications are located in the NApps online repository.
To install this NApp, run:

.. code:: shell

   $ kytos napps install kytos/of_ipv6drop

If you are going to install kytos-napps from source code, all napps will be
installed by default (just remember you need to enable the ones you want
running).
