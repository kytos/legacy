Kytos - kyco-core-napps
=======================

|Tag| |Release| |License|

*Kyco* is the main component of Kytos Project. Kytos Controller (Kyco) uses
*python-openflow* library to parse low level OpenFlow messages.

This repository contains all core network apps used by *Kyco*.

This code is part of *Kytos* project and was developed to be used with *Kytos*
controller.

For more information about, please visit our `Kytos web site
<http://kytos.io/>`__.

Overview
--------

Installation
^^^^^^^^^^^^

You can install this package from source or via pip.

=====================
Installing from PyPI
=====================

*Kyco-core-napps* is in PyPI, so you can easily install it via `pip3` (`pip`
for Python 3) and also include this project in your `requirements.txt`

If you do not have `pip3` you can install it on Ubuntu-base machines by
running:

.. code-block:: shell

    $ sudo apt update
    $ sudo apt install python3-pip


Once you have `pip3`, execute:

.. code:: shell

    sudo pip3 install kyco-core-napps

=======================
Installing source code
=======================

First you need to clone `kyco-core-napps` repository:

.. code-block:: shell

   $ git clone https://github.com/kytos/kyco-core-napps.git

After cloning, the installation process is done by `setuptools` in the usual
way:

.. code-block:: shell

   $ cd kyco-core-napps
   $ sudo python3 setup.py install

Authors
-------

For a complete list of authors, please open `AUTHORS.rst
<docs/toc/AUTHORS.rst>` file.

Contributing
------------

If you want to contribute to this project, please read `CONTRIBUTE.rst
<docs/toc/CONTRIBUTE.rst>`__ and `HACKING.md <docs/toc/HACKING.md>`__ files.

License
-------

This software is under *MIT-License*. For more information please read
``LICENSE`` file.

.. |Tag| image:: https://img.shields.io/github/tag/kytos/kyco-core-napps.svg
   :target: https://github.com/kytos/kyco-core-napps/tags
.. |Release| image:: https://img.shields.io/github/release/kytos/kyco-core-napps.svg
   :target: https://github.com/kytos/kyco-core-napps/releases
.. |License| image:: https://img.shields.io/github/license/kytos/kyco-core-napps.svg
   :target: https://github.com/kytos/kyco-core-napps/blob/master/LICENSE
