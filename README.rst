Kytos - kyco-core-napps
=======================

|Openflow| |Tag| |Release| |Tests| |License|

*Kyco* is the main component of Kytos Project. Kytos Controller (Kyco)
uses *python-openflow* library to parse low level OpenFlow messages.

This repository has all core network apps used by kyco.

This code is part of *Kytos* project and was developed to be used with
*Kytos* controller.

For more information about, please visit our `Kytos web
site <http://kytos.io/>`__.

Installing
----------

You can install this package from source or via pip. If you have cloned
this repository and want to install it via ``setuptools``, please run,
from the cloned directory:

.. code:: shell

    sudo python3 setup.py install

Or, to install via pip, please execute:

.. code:: shell

    sudo pip3 install kyco-core-napps

Authors
-------

This is a collaborative project between SPRACE (From São Paulo State University,
Unesp) and Caltech (California Institute of Technology). For a complete list of
authors, please open `AUTHORS.rst <docs/toc/AUTHORS.rst` file.

Contributing
------------

If you want to contribute to this project, please read `CONTRIBUTE.rst
<docs/toc/CONTRIBUTE.rst>`__ and `HACKING.md <docs/toc/HACKING.md>`__ files.

License
-------

This software is under *MIT-License*. For more information please read
``LICENSE`` file.

.. |Openflow| image:: https://img.shields.io/badge/Openflow-1.0.0-brightgreen.svg
   :target: https://www.opennetworking.org/images/stories/downloads/sdn-resources/onf-specifications/openflow/openflow-spec-v1.0.0.pdf
.. |Tag| image:: https://img.shields.io/github/tag/kytos/kyco.svg
   :target: https://github.com/kytos/kyco/tags
.. |Release| image:: https://img.shields.io/github/release/kytos/kyco.svg
   :target: https://github.com/kytos/kyco/releases
.. |Tests| image:: https://travis-ci.org/kytos/kyco.svg?branch=develop
   :target: https://github.com/kytos/kyco
.. |License| image:: https://img.shields.io/github/license/kytos/kyco.svg
   :target: https://github.com/kytos/kyco/blob/master/LICENSE
