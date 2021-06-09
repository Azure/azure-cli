# Use Azure CLI in Airgapped Clouds

## Introduction
While Azure CLI is not fully supported in an airgapped cloud which has no public internet connectivity, most commands can run without issues if the underlying service is supported in that cloud.

Here is a list of known CLI features that are not supported in airgapped clouds:
* Manage extensions with extension names. For instance, you cannot install the `azure-devops` extension with `az extension add --name azure-devops`.
* `az upgrade` to upgrade Azure CLI to the latest version. Instead, you can follow the below [Install](#Install) instructions to upgrade CLI.
* `az find` to find command examples.
* Command recommendations based on Aladdin service when the command cannot be parsed correctly.
* Commands that install another tool such as `az aks install-cli`, `az storage copy`.
* External channel operations in `az bot` are not available such as Facebook and Wechat.
* Some links in help messages or error messages cannot be accessible.

## Install Azure CLI
We are working on solutions to make the installation and upgrade of Azure CLI easier in airgapped clouds. Before that is ready, you need to download the Azure CLI package with public internet access, copy it to the airgapped cloud environment and then install it locally in the airgapped cloud. You can view all released versions in [Releases](https://github.com/Azure/azure-cli/releases). The top one is the latest release, such as `Azure CLI 2.15.1`.

Package | Download Address | Install Command
--- | --- | ---
DEB | https://packages.microsoft.com/repos/azure-cli/pool/main/a/azure-cli/ | dpkg -i azure-cli_<version\>-1~<distro\>_all.deb
RPM | https://packages.microsoft.com/yumrepos/azure-cli/ | rpm -ivh --nodeps azure-cli-<version\>-*.rpm
MSI | https://azurecliprod.blob.core.windows.net/msi/azure-cli-<version\>.msi | Start-Process msiexec.exe -Wait -ArgumentList '/I azure-cli-<version\>.msi'  

**Note**:
1. Replace `<version>` with the actual CLI version you need to use, such as `2.15.1`. On Ubuntu/Debian, replace `<distro>` with the result of the `lsb_release -cs` command, such as `bionic`.
2. The CLI RPM package depends on a `python3` package and you'll need to install it separately while DEB and MSI packages already have a bundled Python in them.

If you need to install and use Azure CLI in your pipeline, you could upload the Azure CLI package in a storage account that is accessible in the airgapped cloud, then you can download the package from the storage account and install it in your pipeline scripts. For instance, an Azure CLI deb package can be downloaded and installed with the following command:

```bash
curl -Ls -o azure-cli.deb https://mysa.airgapped.cloud.net/packages/azure-cli.deb && dpkg -i azure-cli.deb
```

## Install Extensions
You can download an extension wheel package based on its `downloadUrl` in [index.json](https://github.com/Azure/azure-cli-extensions/blob/master/src/index.json). If the extension does not require extra dependencies (check whether it has the `run_requires` part), use the following command to install it:
```
az extension add --source <local/path/to/the/extension/wheel>
```
Otherwise, you need to figure out the dependency tree of the packages in `run_requires` part using a tool like [pipdeptree](https://pypi.org/project/pipdeptree/). Download all the missing dependency packages that are not already [installed by Azure CLI](https://github.com/Azure/azure-cli/blob/master/src/azure-cli/requirements.py3.Linux.txt) from https://pypi.org/ and use `pip` to install the extension without dependencies in the default extension directory and then install all dependency packages locally. Take `azure-devops` as an example, it requires
```
"distro (==1.3.0)",
"msrest (<0.7.0,>=0.6.0)",
"python-dateutil (==2.7.3)"
```

We can first download `azure-devops` wheel from https://github.com/Azure/azure-devops-cli-extension/releases/download/20190805.1/azure_devops-0.12.0-py2.py3-none-any.whl after looking up in the [index.json](https://github.com/Azure/azure-cli-extensions/blob/master/src/index.json). For dependencies, a compatible version of `msrest` is already installed by Azure CLI as it is in the [requirements.txt](https://github.com/Azure/azure-cli/blob/master/src/azure-cli/requirements.py3.Linux.txt). `pipdeptree -p distro` shows that `distro` has no dependencies and we can download it from https://pypi.org/project/distro/1.3.0/#files. `pipdeptree -p python-dateutil` shows `python-dateutil` depends on `six` and `six` is already installed by Azure CLI. We only need to download `python-dateutil` from https://pypi.org/project/python-dateutil/2.7.3/#files.

Therefore, `azure-devops` can be installed with the following commands (assuming packages are already downloaded in the home directory):

```
$ pip install --no-deps ~/azure_devops-0.12.0-py2.py3-none-any.whl --target ~/.azure/cliextensions/azure-devops
$ pip install --no-deps ~/distro-1.3.0-py2.py3-none-any.whl --target ~/.azure/cliextensions/azure-devops
$ pip install --no-deps ~/python_dateutil-2.7.3-py2.py3-none-any.whl --target ~/.azure/cliextensions/azure-devops
```

## Load Cloud Endpoints
If you are working in an Azure AirGapped Cloud, you should be able to get a cloud metadata URL from its documentation. You can set the environment variable `ARM_CLOUD_METADATA_URL` to this URL with:
```bash
export ARM_CLOUD_METADATA_URL=https://example.url.com/metadata/endpoints?api-version=2019-05-01
```
on Linux shells or
```powershell
$Env:ARM_CLOUD_METADATA_URL = "https://example.url.com/metadata/endpoints?api-version=2019-05-01"
```
on Windows Powershell.
The content of the metadata URL should be similar to that of the public cloud metadata URL: https://management.azure.com/metadata/endpoints?api-version=2019-05-01.

Then CLI will load the available clouds and the corresponding cloud endpoints from the URL. The first cloud in the available cloud list will be set as the active cloud by default if the public `AzureCloud` is (most likely) not available.

If you are working with multiple clouds, you can learn more in [Work with multiple clouds](https://docs.microsoft.com/cli/azure/manage-clouds-azure-cli).

## Set CA bundle certificate
Please follow the first solution in [Work behind a proxy](https://docs.microsoft.com/cli/azure/use-cli-effectively#work-behind-a-proxy) to set up the certificate in your airgapped cloud environment. For more details, you can also refer to the steps in the [guide](https://docs.microsoft.com/azure-stack/user/azure-stack-version-profiles-azurecli2) to set up CLI for Azure Stack Hub.

## Login with service principal
Use the service principal that was granted permission to access a subscription in the airgapped cloud to login.

```azurecli
az login --service-principal -u <service principal id> -p <service principal password> --tenant <tenant id>
```

## Run CLI Commands
If you meet any issues while running Azure CLI commands in airgapped clouds, please provide feedback through [Github issues](https://github.com/Azure/azure-cli/issues/new?assignees=&labels=&template=Bug_report.md&title=).
