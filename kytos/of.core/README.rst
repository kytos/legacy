Overview
========

The app **of.core** is a app responsible to handle OpenFlow basic
operations.The main handle messages are:

-  reply and request hello messages;
-  reply echo request messages;
-  request stats messages;
-  send a feature request after echo reply;
-  update flow list of each switch;
-  update features;
-  handle all input messages;

Requirements
============

All requirements is installed using the *requirements.txt* packages.

Installing
==========

This is a default Kytos Network Application and the installation process is
straight forward: Just copy the ``kytos/of.core`` directory to your napps
directory. The default path is ``/var/lib/kytos/napps/``.

.. note:: Please note that you must copy from the root of the napp (including
    the ``kyto`` folder). So you will have
    ``/var/lib/kytos/napps/kytos/of.core`` at the end.

If you are going to install the whole repository, with all napps, you do not
have to worry about the above procedings, since all napps will be copied into
the correct napps folder during the installation process.

