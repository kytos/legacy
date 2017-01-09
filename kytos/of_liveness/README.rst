Overview
========

The **of.liveness** is a application responsible to keep track of KycoSwitches
and check if their liveness. To do this, the application sends echo request
to network and keep waiting echo reply packets from switches. In addition
verifies all messages received by Kyco from KycoSwitches to update the lastseen.

Installing
==========

This is a default Kytos Network Application and the installation process is
straight forward: Just copy the ``kytos/of.liveness`` directory to your napps
directory. The default path is ``/var/lib/kytos/napps/``.

.. note:: Please note that you must copy from the root of the napp (including
    the ``kyto`` folder). So you will have
    ``/var/lib/kytos/napps/kytos/of.liveness`` at the end.

If you are going to install the whole repository, with all napps, you do not
have to worry about the above procedings, since all napps will be copied into
the correct napps folder during the installation process.
