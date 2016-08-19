Microsoft Project AZ - Preview
==================================

.. image:: https://travis-ci.org/Azure/azure-cli.svg?branch=master
    :target: https://travis-ci.org/Azure/azure-cli

A great cloud needs great tools; we're excited to introduce *Project Az*, our prototype for building a great, multiplatform commandline experience for Azure.

Project Az is built on Python (2.7, 3.4 and 3.5).

Installation
============

For installation steps for common platforms, please take a look at our `preview installation guide <http://github.com/Azure/azure-cli/blob/master/doc/preview_install_guide.md>`__.

Docker Setup (optional)
-----------------------
We have automated Docker images of the latest code in the master branch.

If you have not previously done so, `configure your Docker client engine <https://docs.docker.com/engine/installation/>`__.

Then:
 + Run :code:`docker pull azuresdk/azure-cli-python:latest`
 + Run :code:`docker run -it azuresdk/azure-cli-python:latest`

Alternatively:
 + Run :code:`docker pull azuresdk/azure-cli-python:latest`
 + Run :code:`alias az='docker run --rm -v ~/.azure2:/root/.azure azuresdk/azure-cli-python az'`
 + Then run :code:`az` as normal. e.g. :code:`az account login`

Usage
=====
    
.. code-block:: console

    $ az [ group ] [ subgroup ] [ command ] {parameters}

For sample scripts and commands, please visit the `Demo Scripts <https://github.com/Azure/azure-cli/blob/master/doc/preview_demo_scripts.md>`__ page.  

Download Source Code
====================

To get the source code of the SDK via **git** type

.. code-block:: console
    
    $ git clone https://github.com/Azure/azure-cli.git



Reporting issues and feedback
=======================================

If you encounter any bugs with the tool please file an issue in the `Issues <https://github.com/Azure/azure-cli/issues>`__ section of our GitHub repo.

To provide feedback from the command line, try the ``az feedback`` command.

Contribute Code
===================================

This project has adopted the `Microsoft Open Source Code of Conduct <https://opensource.microsoft.com/codeofconduct/>`__.

For more information see the `Code of Conduct FAQ <https://opensource.microsoft.com/codeofconduct/faq/>`__ or contact `opencode@microsoft.com <mailto:opencode@microsoft.com>`__ with any additional questions or comments.

If you would like to become an active contributor to this project please
follow the instructions provided in `Microsoft Azure Projects Contribution Guidelines <http://azure.github.io/guidelines.html>`__

Learn More
==========

`Microsoft Azure Python Developer Center <http://azure.microsoft.com/en-us/develop/python/>`__

License
=======

`MIT <https://github.com/Azure/azure-cli/blob/master/LICENSE.txt>`__
