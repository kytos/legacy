Overview
========

The *of.ipv6drop* network application (NApp) install a flow on the
connected switches so that they *DROP* all ipv6 incoming packets. Once
the NApp is loaded on the controller it work by itself, without the need
of any user interaction.

To do so, the NApp listen to all ``kyco/core.switches.new`` events (that
represents a new switch connected) and send to this switch a FlowMod
message to install the DROP IPv6 flow (match ``dl_type`` == ``0x86dd``).
