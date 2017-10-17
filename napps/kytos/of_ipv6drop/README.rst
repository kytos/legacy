Overview
========

The *of_ipv6drop* network application (NApp) installs a flow on all connected
switches for them to *DROP* all ipv6 incoming packets. Once the NApp is loaded
on the controller it works by itself, without the need of any interaction.

To do so, the NApp listens to all ``kytos/core.switch.new`` events (which
represent a new switch has connected) and send to this switch a FlowMod message
to install the DROP IPv6 flow (match ``dl_type`` == ``0x86dd``).

Requirements
============

All requirements are listed in *requirements.txt*.

Installing
==========

All of the Kytos Network Applications are located in the NApps online
repository. To install this NApp, run:

.. code:: shell

   $ kytos napps install legacy/of_ipv6drop

If you are going to install kytos-napps from source code, all napps will be
installed by default (just remember you need to enable the ones you want
running).
