Overview
========

The *of.ipv6drop* network application (NApp) install a flow on the
connected switches so that they *DROP* all ipv6 incoming packets. Once
the NApp is loaded on the controller it work by itself, without the need
of any user interaction.

To do so, the NApp listen to all ``kyco/core.switches.new`` events (that
represents a new switch connected) and send to this switch a FlowMod
message to install the DROP IPv6 flow (match ``dl_type`` == ``0x86dd``).

Requirements
============

All requirements is installed using the *requirements.txt* packages.

Installing
==========

This is a default Kytos Network Application and the installation process is
straight forward: Just copy the ``kytos/of_ipv6drop`` directory to your napps
directory. The default path is ``/var/lib/kytos/napps/``.

.. note:: Please note that you must copy from the root of the napp (including
    the ``kyto`` folder). So you will have
    ``/var/lib/kytos/napps/kytos/of_ipv6drop`` at the end.

If you are going to install the whole repository, with all napps, you do not
have to worry about the above procedings, since all napps will be copied into
the correct napps folder during the installation process.
