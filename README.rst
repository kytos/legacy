#########
ATTENTION
#########
THIS REPOSITORY CONTAINS THE LEGACY NETWORK APPLICATIONS (NAPPS) DEVELOPED BY
KYTOS TEAM, PREVIOUSLY THIS WAS THE 'KYTOS-NAPPS' REPOSITORY. ALL NAPPS HERE
ARE HOSTED ON NAPPS.KYTOS.IO SERVER UNDER THE USERNAME 'legacy'.


########
Overview
########

|Experimental| |Tag| |Release| |License| |Build| |Coverage| |Quality|


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

NApps are installed and configured using
`kytos-utils <https://github.com/kytos/kytos-utils>`__

We are doing a huge effort to make Kytos and its components available on all
common distros. So, we recommend you to download it from your distro repository.

To install a specific NApp, run:

.. code-block:: shell

   $ kytos napps install <napp>

The NApp will be downloaded and installed automatically from the online
repository if it is not found in the local system.

Of course, if you are trying to test, develop or just want a more recent version
of our software, no problem: Download now the latest release (it still a beta
software) from our repository. This will download and install all the currently
available NApps.

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
please refer to `kytos-utils <https://github.com/kytos/kytos-utils>`__.

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
.. |Build| image:: https://scrutinizer-ci.com/g/kytos/kytos-napps/badges/build.png?b=master
  :alt: Build status
  :target: https://scrutinizer-ci.com/g/kytos/kytos-napps/?branch=master
.. |Coverage| image:: https://scrutinizer-ci.com/g/kytos/kytos-napps/badges/coverage.png?b=master
  :alt: Code coverage
  :target: https://scrutinizer-ci.com/g/kytos/kytos-napps/?branch=master
.. |Quality| image:: https://scrutinizer-ci.com/g/kytos/kytos-napps/badges/quality-score.png?b=master
  :alt: Code-quality score
  :target: https://scrutinizer-ci.com/g/kytos/kytos-napps/?branch=master
