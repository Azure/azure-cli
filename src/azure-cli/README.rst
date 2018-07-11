Microsoft Azure CLI
===================

A great cloud needs great tools; we're excited to introduce *Azure CLI*, our next generation multi-platform command line experience for Azure.

Usage
=====
.. code-block:: console

    $ az [ group ] [ subgroup ] [ command ] {parameters}


Getting Started
=====================

After installation, use the ``az configure`` command to help setup your environment.

.. code-block:: console

   $ az configure

For usage and help content, pass in the ``-h`` parameter, for example:

.. code-block:: console

   $ az storage -h
   $ az vm create -h

Highlights
===========

Here are a few features and concepts that can help you get the most out of the Azure CLI.

The following examples are showing using the ``--output table`` format, you can change your default using the ``$ az configure`` command.

Tab Completion
++++++++++++++

We support tab-completion for groups, commands, and some parameters

.. code-block:: console

   # looking up resource group and name
   $ az vm show -g [tab][tab]
   AccountingGroup   RGOne  WebPropertiesRG
   $ az vm show -g WebPropertiesRG -n [tab][tab]
   StoreVM  Bizlogic
   $ az vm show -g WebPropertiesRG -n Bizlogic

Querying
++++++++

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
+++++++++++++++++++++++
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
+++++++++++++++++++++++++
For more usage examples, take a look at our `GitHub samples repo <http://github.com/Azure/azure-cli-samples>`__.

Reporting issues and feedback
=======================================

If you encounter any bugs with the tool please file an issue in the `Issues <https://github.com/Azure/azure-cli/issues>`__ section of our GitHub repo.

To provide feedback from the command line, try the ``az feedback`` command.

License
=======

`MIT <https://github.com/Azure/azure-cli/blob/master/LICENSE.txt>`__
