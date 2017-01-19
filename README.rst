Microsoft Azure CLI 2.0 - Preview
==================================

.. image:: https://img.shields.io/pypi/pyversions/azure-cli.svg?maxAge=2592000
    :target: https://pypi.python.org/pypi/azure-cli

.. image:: https://travis-ci.org/Azure/azure-cli.svg?branch=master
    :target: https://travis-ci.org/Azure/azure-cli

A great cloud needs great tools; we're excited to introduce *Azure CLI 2.0 - Preview*, our next generation multi-platform command line experience for Azure.

Installation
===============

A list of common install issues and their resolutions are available at `install troubleshooting <https://github.com/Azure/azure-cli/blob/master/doc/install_troubleshooting.md>`__.

**How would you like to install?**

- `Interactive install script <#interactive-install-script>`__
- `Pip <#pip>`__
- `Apt-get <#apt-get>`__
- `Homebrew <#homebrew>`__
- `Docker <#docker-versioned>`__
- `Nightly Builds <#nightly-builds>`__
- `Developer Setup <#developer-setup>`__

Interactive install script
^^^^^^^^^^^^^^^^^^^^^^^^^^

On Windows, install via `pip <#pip>`__.

On Linux, see our `prerequisites <https://github.com/Azure/azure-cli/blob/master/doc/install_linux_prerequisites.md>`__ then install as follows:

.. code-block:: console

   $ curl -L https://aka.ms/InstallAzureCli | bash

or:

.. code-block:: console

   $ wget -q -O - https://aka.ms/InstallAzureCli | bash

Install additional components with ``$ az component update --add <component_name>``

Pip
^^^

On Linux, see our `prerequisites <https://github.com/Azure/azure-cli/blob/master/doc/install_linux_prerequisites.md>`__.

.. code-block:: console

   $ pip install --user azure-cli

Install additional components with ``$ az component update --add <component_name>``

Enable tab completion with ``source az.completion.sh`` (not available on Windows CMD).

You may need to modify your PATH:

    **Linux**

    ``$ export PATH=$PATH:~/.local/bin``

    **OS X**

    ``export PATH=$PATH:~/Library/Python/X.Y/bin``

    **Windows**

    Add ``%APPDATA%\PythonXY\Scripts`` to your PATH.

    Where X, Y is your Python version.

Apt-get
^^^^^^^

For Debian/Ubuntu based systems.

First, modify your sources list:

    **32 bit system**

    ``$ echo "deb https://apt-mo.trafficmanager.net/repos/azure-cli/ wheezy main" | sudo tee /etc/apt/sources.list.d/azure-cli.list``

    **64 bit system**

    ``$ echo "deb [arch=amd64] https://apt-mo.trafficmanager.net/repos/azure-cli/ wheezy main" | sudo tee /etc/apt/sources.list.d/azure-cli.list``

Run the following:

.. code-block:: console

    $ sudo apt-key adv --keyserver apt-mo.trafficmanager.net --recv-keys 417A0893
    $ sudo apt-get install apt-transport-https
    $ sudo apt-get update && sudo apt-get install azure-cli

Homebrew
^^^^^^^^

(Pending merge of https://github.com/Homebrew/homebrew-core/pull/8669)

For macOS systems.

.. code-block:: console

    $ brew install azure-cli-2

Docker (versioned)
^^^^^^^^^^^^^^^^^^

We maintain a Docker image preconfigured with the Azure CLI.

.. code-block:: console

   $ docker run -v ${HOME}:/root -it azuresdk/azure-cli-python:<version>

See our `Docker tags <https://hub.docker.com/r/azuresdk/azure-cli-python/tags/>`__ for available versions.

Docker (automated)
^^^^^^^^^^^^^^^^^^

Run the latest automated Docker build with the command below.

.. code-block:: console

   $ docker run -v ${HOME}:/root -it azuresdk/azure-cli-python:latest

All command modules are included in this version as the image is built directly from the Git repository.

Nightly Builds
^^^^^^^^^^^^^^

Install nightly builds with pip in a virtual environment.

.. code-block:: console

   $ pip install --pre azure-cli --extra-index-url https://azureclinightly.blob.core.windows.net/packages

- Builds happen at 21:00:00 PDT each night. They are published shortly afterwards.
- Whilst all command modules are built each night, not all are included on install.
- Install additional components with:

.. code-block:: console

    $ export AZURE_COMPONENT_PACKAGE_INDEX_URL=https://azureclinightly.blob.core.windows.net/packages
    $ az component update --add <component_name> --private

- To view the list of installed packages, run ``az component list``

Developer Setup
^^^^^^^^^^^^^^^
If you would like to setup a development environment and contribute to the CLI, see `Configuring Your Machine <https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md>`__.


Usage
=====
.. code-block:: console

    $ az [ group ] [ subgroup ] [ command ] {parameters}


Getting Started
=====================

After installation, use the ``az configure`` command to help set up your environment and get you logged in.

.. code-block:: console

   $ az configure

For usage and help content, pass in the ``-h`` parameter, for example:

.. code-block:: console

   $ az storage -h
   $ az vm create -h

Highlights
===========

Here are a few features and concepts that can help you get the most out of the Azure CLI 2.0 Preview

.. image:: doc/assets/AzBlogAnimation4.gif
    :align: center
    :alt: Azure CLI 2.0 Highlight Reel
    :width: 600
    :height: 300


The following examples are showing using the ``--output table`` format, you can change your default using the ``$ az configure`` command.

Tab Completion
^^^^^^^^^^^^^^

We support tab-completion for groups, commands, and some parameters

.. code-block:: console

   # looking up resource group and name
   $ az vm show -g [tab][tab]
   AccountingGroup   RGOne  WebPropertiesRG
   $ az vm show -g WebPropertiesRG -n [tab][tab]
   StoreVM  Bizlogic
   $ az vm show -g WebPropertiesRG -n Bizlogic

Querying
^^^^^^^^

You can use the ``--query`` parameter and the JMESPath query syntax to customize your output.

.. code-block:: console

   $ az vm list --query '[].{name:name,os:storageProfile.osDisk.osType}'
   Name                    Os
   ----------------------  -------
   storevm                 Linux
   bizlogic                Linux
   demo32111vm             Windows
   dcos-master-39DB807E-0  Linux

Creating a new Linux VM
^^^^^^^^^^^^^^^^^^^^^^^
The following block creates a new resource group in the 'westus' region, then creates a new Ubuntu VM.  We automatically provide a series of smart defaults, such as setting up SSH with your  ``~/.ssh/id_rsa.pub`` key.  For more details, try ``az vm create -h``.

.. code-block:: console

   $ az group create -l westus -n MyGroup
   Name     Location
   -------  ----------
   MyGroup  westus

   $ az vm create -g MyGroup -n MyVM --image ubuntults
   MacAddress         ResourceGroup    PublicIpAddress    PrivateIpAddress
   -----------------  ---------------  -----------------  ------------------
   00-0D-3A-30-B2-D7  MyGroup          52.160.111.118     10.0.0.4

   $ ssh 52.160.111.118
   Welcome to Ubuntu 14.04.4 LTS (GNU/Linux 3.19.0-65-generic x86_64)

   System information as of Thu Sep 15 20:47:31 UTC 2016

   System load: 0.39              Memory usage: 2%   Processes:       80
   Usage of /:  39.6% of 1.94GB   Swap usage:   0%   Users logged in: 0

   jasonsha@MyVM:~$

More Samples and Snippets
^^^^^^^^^^^^^^^^^^^^^^^^^
For more usage examples, take a look at our `GitHub samples repo <http://github.com/Azure/azure-cli-samples>`__.

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

License
=======

`MIT <https://github.com/Azure/azure-cli/blob/master/LICENSE.txt>`__
