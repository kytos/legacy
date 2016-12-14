|Experimental| |Openflow| |Pypi| |Tag| |Release| |License|

========
Overview
========

Core Network Applications(*NApps*) is part of *Kytos* project and was
developed to be used with `Kytos Controller <http://github.com/kytos/kyco>`__.
This repository contain only NApps developed by Kytos community. If you want
develop yours NApps to use with Kytos you want create your own repository too.

For more information about, please visit our `Kytos web site
<http://kytos.io/>`__.

QuickStart
----------

There are two ways to install this package, from source (if you have cloned
this repository) or via pip.

Installing from PyPI
++++++++++++++++++++

*Kyco-core-napps* is in PyPI, so you can easily install it via `pip3` (`pip`
for Python 3) and also include this project in your `requirements.txt`

If you do not have `pip3`, the procedures to install are:

Ubuntu/Debian
=============

.. code-block:: shell

    $ sudo apt-get update
    $ sudo apt-get install python3-pip

Fedora
======

.. code-block:: shell

    $ sudo dnf update
    $ sudo dnf install python3-pip

Centos
======

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
+++++++++++++++++++++++++++

First you need to clone `kyco-core-napps` repository:

.. code-block:: shell

   $ git clone https://github.com/kytos/kyco-core-napps.git

After cloning, the installation process is done by `setuptools` in the usual
way:

.. code-block:: shell

   $ cd kyco-core-napps
   $ sudo python3 setup.py install

Configuring
-----------

After *Kyco-core-napps* installation, this package create a folder at
``/var/lib/kytos/napps`` where, by default, all networks applications are
installed and working when *Kyco* is running. For kytos NApps there are a
folder at ``/var/lib/kytos/napps/kytos/`` with all NApps from this repository.

.. note:: When a napps have a experimental tag means that this napps doesn't
   working properly yet.

Authors
-------

For a complete list of authors, please open `AUTHORS <AUTHORS.rst>`__ file.

License
-------

This software is under *MIT-License*. For more information please read
`LICENSE <LICENCE>`__ file.

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
