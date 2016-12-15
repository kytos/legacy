|Experimental| |Openflow| |Pypi| |Tag| |Release| |License|

########
Overview
########

Core Network Applications(*NApps*) is part of *Kytos* project and was developed
to be used with `Kytos Controller <http://github.com/kytos/kyco>`__.  This
repository contain only NApps developed by Kytos core team.

Beside this Napps, new applications can be developed by third-part and may not
be maintened by the core team. But of course that we support this and we provide
a repository infrastructure so you can upload and share your napp.

So basically this is a small set of Network Apps that is installed on your
controller by default. Here you can learn how to enable and disable them as well
as you will learn what is each one's scope.

Please, feel free to use them as a starting point and reference for your own
Napps.

.. note:: When a napps have a experimental tag means that this napps doesn't
   working properly yet.

QuickStart
**********

There are two ways to install this package, from source (if you have cloned
this repository) or via pip.

And here, basically the install process is: a) install the requirements and b)
copy all napps to a specific folder, so the controller can load them.

Installing from PyPI
====================

*Kyco-core-napps* is in PyPI, so you can easily install it via `pip3` (`pip`
for Python 3) and also include this project in your `requirements.txt`

If you do not have `pip3`, the procedures to install are:

Ubuntu/Debian
-------------

.. code-block:: shell

    $ sudo apt-get update
    $ sudo apt-get install python3-pip

Fedora
------

.. code-block:: shell

    $ sudo dnf update
    $ sudo dnf install python3-pip

Centos
------

.. code-block:: shell

    $ sudo yum -y update
    $ sudo yum -y install yum-utils
    $ sudo yum -y groupinstall development
    $ sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
    $ sudo yum -y install python35u-3.5.2
    $ sudo curl https://bootstrap.pypa.io/get-pip.py | python3.5

After installed `pip3` you can install *Kyco-core-napps* running:

.. code:: shell

    $ sudo pip3 install kyco-core-napps

Installing from source code
===========================

First you need to clone `kyco-core-napps` repository:

.. code-block:: shell

   $ git clone https://github.com/kytos/kyco-core-napps.git

After cloning, the installation process is done by `setuptools` in the usual
way:

.. code-block:: shell

   $ cd kyco-core-napps
   $ sudo python3 setup.py install

Configuring
***********

After *Kyco-core-napps* installation, this package copy all core napps to
``/var/lib/kytos/napps/kytos/`` where, by default, all networks applications are
loaded when *Kyco* is started.

Please configure your controller to point to the root of this folder
(``/var/lib/kytos/napps/`` in order to load theses napps.

You can also feel free to move this folder to another place into your system,
but please remember to change this on your controller config file. For more
information please visit the section "Configuration" on the `Kyco's
Administrator Guide <http://docs.kytos.io/kyco/administrator/#configuration>`__.

.. |Experimental| image:: https://img.shields.io/badge/stability-experimental-orange.svg
.. |Openflow| image:: https://img.shields.io/badge/Openflow-1.0.0-brightgreen.svg
   :target: https://www.opennetworking.org/images/stories/downloads/sdn-resources/onf-specifications/openflow/openflow-spec-v1.0.0.pdf
.. |Pypi| image:: https://img.shields.io/pypi/v/kyco-core-napps.svg
.. |Tag| image:: https://img.shields.io/github/tag/kytos/kyco-core-napps.svg
   :target: https://github.com/kytos/kyco-core-napps/tags
.. |Release| image:: https://img.shields.io/github/release/kytos/kyco-core-napps.svg
   :target: https://github.com/kytos/kyco-core-napps/releases
.. |License| image:: https://img.shields.io/github/license/kytos/kyco-core-napps.svg
   :target: https://github.com/kytos/kyco-core-napps/blob/master/LICENSE
