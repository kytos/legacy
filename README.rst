########
Overview
########

|Experimental| |Tag| |Release| |License|


Network Applications(*NApps*) is part of `Kytos project <https://kytos.io/>`__
and was developed to be used with it. This repository contain only NApps
developed by Kytos core team.

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

Installing
==========

We are doing a huge effort to make Kytos and its components available on all
common distros. So, we recommend you to download it from your distro repository.

But if you are trying to test, develop or just want a more recent version of
our software no problem: Download now, the latest release (it still a beta
software), from our repository:


First you need to clone *kytos-napps* repository:

.. code-block:: shell

   $ git clone https://github.com/kytos/kytos-napps.git

After cloning, the installation process is done by `setuptools` in the usual
way:

.. code-block:: shell

   $ cd kytos-napps
   $ sudo python3 setup.py install

Configuring
***********

After *kytos-napps* installation, this package copy all core napps to
``/var/lib/kytos/napps/kytos/`` where, by default, all networks applications are
loaded when your Kytos controller is started.

Please configure your controller to point to the root of this folder
(``/var/lib/kytos/napps/`` in order to load theses napps.

You can also feel free to move this folder to another place into your system,
but please remember to change this on your controller config file. For more
information please visit the section "Configuration" on the `Kytos's
Administrator Guide
<https://docs.kytos.io/kytos/administrator/#configuration>`__.

Authors
*******

For a complete list of authors, please open ``AUTHORS.rst`` file.

Contributing
************

If you want to contribute to this project, please read `Kytos Documentation
<https://docs.kytos.io/kytos/contributing/>`__ website.

License
*******

This software is under *MIT-License*. For more information please read
``LICENSE`` file.

.. |Experimental| image:: https://img.shields.io/badge/stability-experimental-orange.svg
.. |Tag| image:: https://img.shields.io/github/tag/kytos/kytos-napps.svg
   :target: https://github.com/kytos/kytos-napps/tags
.. |Release| image:: https://img.shields.io/github/release/kytos/kytos-napps.svg
   :target: https://github.com/kytos/kytos-napps/releases
.. |License| image:: https://img.shields.io/github/license/kytos/kytos-napps.svg
   :target: https://github.com/kytos/kytos-napps/blob/master/LICENSE
