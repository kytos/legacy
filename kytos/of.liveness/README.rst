Overview
========

The **of.liveness** is a application responsible to keep track of KycoSwitches
and check if their liveness. To do this, the application sends echo request
to network and keep waiting echo reply packets from switches. In addition
verifies all messages received by Kyco from KycoSwitches to update the lastseen.
