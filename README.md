# Microsoft Azure CLI 2.0

[![Python](https://img.shields.io/pypi/pyversions/azure-cli.svg?maxAge=2592000)](https://pypi.python.org/pypi/azure-cli)
[![Travis](https://travis-ci.org/Azure/azure-cli.svg?branch=master)](https://travis-ci.org/Azure/azure-cli)
[![Slack](https://azureclislackin.azurewebsites.net/badge.svg)](https://azurecli.slack.com)

A great cloud needs great tools; we're excited to introduce *Azure CLI 2.0*, our next generation multi-platform command line experience for Azure.

## Installation

```bash
$ curl -L https://aka.ms/InstallAzureCli | bash
```

Please refer to the [install guide](https://docs.microsoft.com/en-us/cli/azure/install-az-cli2) for detailed install instructions.

A list of common install issues and their resolutions are available at [install troubleshooting](https://github.com/Azure/azure-cli/blob/master/doc/install_troubleshooting.md).

### Developer Installation (see below)

- [Docker](#docker)
- [Nightly Builds](#nightly-builds)
- [Developer Setup](#developer-setup)

## Usage

```bash
$ az [ group ] [ subgroup ] [ command ] {parameters}
```

### Get Started

Please refer to the ["get started" guide](https://docs.microsoft.com/en-us/cli/azure/get-started-with-az-cli2) for in-depth instructions.

For usage and help content, pass in the `-h` parameter, for example:

```bash
$ az storage -h
$ az vm create -h
```

### Highlights

Here are a few features and concepts that can help you get the most out of the Azure CLI 2.0

![Azure CLI 2.0 Highlight Reel](doc/assets/AzBlogAnimation4.gif)

The following examples are showing using the `--output table` format, you can change your default using the `az configure` command.

#### Tab Completion

We support tab-completion for groups, commands, and some parameters

```bash
# looking up resource group and name
$ az vm show -g [tab][tab]
AccountingGroup   RGOne  WebPropertiesRG

$ az vm show -g WebPropertiesRG -n [tab][tab]
StoreVM  Bizlogic

$ az vm show -g WebPropertiesRG -n Bizlogic
```

#### Query

You can use the `--query` parameter and the [JMESPath](http://jmespath.org/) query syntax to customize your output.

```bash
$ az vm list --query "[?provisioningState=='Succeeded'].{ name: name, os: storageProfile.osDisk.osType }"
Name                    Os
----------------------  -------
storevm                 Linux
bizlogic                Linux
demo32111vm             Windows
dcos-master-39DB807E-0  Linux
```

#### Creating a VM
The following block creates a new resource group in the 'westus' region, then creates a new Ubuntu VM.  We automatically provide a series of smart defaults, such as setting up SSH with your  `~/.ssh/id_rsa.pub` key.  For more details, try `az vm create -h`.

```bash
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
```

#### More Samples and Snippets
For more usage examples, take a look at our [GitHub samples repo](http://github.com/Azure/azure-cli-samples) or [https://docs.microsoft.com/en-us/cli/azure/overview](https://docs.microsoft.com/en-us/cli/azure/overview).

## Reporting issues and feedback

If you encounter any bugs with the tool please file an issue in the [Issues](https://github.com/Azure/azure-cli/issues) section of our GitHub repo.

To provide feedback from the command line, try the `az feedback` command!

## Developer Installation

### Docker

**This install does not support the component feature.**

We maintain a Docker image preconfigured with the Azure CLI.  Run the latest automated Docker build with the command below.

```bash
$ docker run -v ${HOME}:/root -it azuresdk/azure-cli-python:latest
```

All command modules are included in this version as the image is built directly from the Git repository.  
You can also get a specific version of Azure CLI 2.0 via Docker.

```bash
$ docker run -v ${HOME}:/root -it azuresdk/azure-cli-python:<version>
```

See our [Docker tags](https://hub.docker.com/r/azuresdk/azure-cli-python/tags/) for available versions.

### Nightly Builds

Install nightly builds with pip in a virtual environment.

```bash
$ pip install --pre azure-cli --extra-index-url https://azureclinightly.blob.core.windows.net/packages
```

To upgrade your current nightly build pass the `--upgrade` option.

```bash
$ pip install --upgrade --pre azure-cli --extra-index-url https://azureclinightly.blob.core.windows.net/packages
```

- Builds happen at 21:00:00 PDT each night. They are published shortly afterwards.
- Whilst all command modules are built each night, not all are included on install.
- Install additional components with:  
    ```
    $ export AZURE_COMPONENT_PACKAGE_INDEX_URL=https://azureclinightly.blob.core.windows.net/packages
    ```  
    ```
    $ az component update --add <component_name> --private
    ```
- To view the list of installed packages, run ``az component list``

## Developer Setup
If you would like to setup a development environment and contribute to the CLI, see 
[Configuring Your Machine](https://github.com/Azure/azure-cli/blob/master/doc/configuring_your_machine.md).

## Contribute Code

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).

For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

If you would like to become an active contributor to this project please
follow the instructions provided in [Microsoft Azure Projects Contribution Guidelines](http://azure.github.io/guidelines.html).

## License

```
Azure CLI

Copyright (c) Microsoft Corporation

All rights reserved. 

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the ""Software""), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

## Automation

- [How to write scenario based VCR test](https://github.com/Azure/azure-cli/blob/master/doc/scenario_base_tests.md)
