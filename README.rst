########
Overview
########

|Experimental| |Tag| |Release| |License|


Network Applications(*NApps*) are part of `Kytos project <https://kytos.io/>`__
and were developed to be used with it. This repository contain only NApps
developed by Kytos core team.

Besides these NApps, new applications can be written by third party developers
and may not be maintained by the core team. Of course, we support this and
provide a repository infrastructure so everyone can upload and share their
NApps.

Basically this is a small set of Network Apps that is installed for your Kytos
controller by default.

Please, feel free to use them as a starting point and reference for your own
NApps.

.. note:: When a NApp has an experimental tag, it means that the NApp isn't
   working properly yet.

QuickStart
**********

Installing
==========

We are doing a huge effort to make Kytos and its components available on all
common distros. So, we recommend you to download it from your distro repository.

But if you are trying to test, develop or just want a more recent version of
our software, no problem: Download now the latest release (it still a beta
software) from our repository:


First you need to clone *kytos-napps* repository:

.. code-block:: shell

   $ git clone https://github.com/kytos/kytos-napps.git

After cloning, the installation process is done by `setuptools` in the usual
way:

.. code-block:: shell

   $ cd kytos-napps
   $ sudo python3.6 setup.py install

Configuring
***********

After *kytos-napps* installation, this package copies NApps to
``/var/lib/kytos/napps/`` (your controller's NApps folder is configured to
point to this directory). Enabled NApps are located in
``/var/lib/kytos/napps/kytos/`` and are loaded when your Kytos controller is
started.

Feel free to move this folder to another place in your system, but please
remember to change this on your controller config file. For more information
please visit the section "Configuration" on the `Kytos's Administrator Guide
<https://docs.kytos.io/kytos/administrator/#configuration>`__.

For information about enabling or disabling NApps for the Kytos controller,
please refer to `kytos-utils <https://github.com/kytos/kytos-napps>`__.

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
