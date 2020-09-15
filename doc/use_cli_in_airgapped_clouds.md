# Use Azure CLI in Airgapped Clouds

## Introduction
While Azure CLI is not fully supported in an airgapped cloud which has no public internet connectivity, most commands could run without issues if the underlying service is supported in that cloud.

## Install
We are working on solutions to make Azure CLI more available in airgapped clouds. Before that is ready, you are on your own to download the Azure CLI package with public internet access, copy it to the airgapped cloud environment and then install it locally in the airgapped cloud.

Package | Download Address | Install Command
--- | --- | ---
DEB | https://packages.microsoft.com/repos/azure-cli/pool/main/a/azure-cli/ | dpkg -i azure-cli_*.deb
RPM | https://packages.microsoft.com/yumrepos/azure-cli/ | rpm -ivh --nodeps azure-cli-*.rpm
MSI | https://azurecliprod.blob.core.windows.net/msi/azure-cli-2.x.x.msi | Start-Process msiexec.exe -Wait -ArgumentList '/I azure-cli-2.x.x.msi'  

If you need to install and use Azure CLI in your pipeline, you could upload the Azure CLI package in a storage account that is accessible in the airgapped cloud, then you can download the package from the storage account and install it in your pipeline scripts. For instance, an Azure CLI deb package could be downloaded and installed with the following command:
```
curl -Ls -o azure-cli.deb https://mysa.airgapped.cloud.net/packages/azure-cli.deb  && dpkg -i azure-cli.deb
```


## Load Cloud Endpoints
If you are working in an Azure Airgapped Cloud such as `USSec` or `USNat`, you should be able to get a cloud metadata URL from its documentation. You can set the environment variable `ARM_CLOUD_METADATA_URL` to this URL, then CLI will load the available clouds and the corresponding cloud endpoints from the URL. The first cloud in the available cloud list will be set as the active cloud by default if the public `AzureCloud` is (most likely) not available.

If you are working with multiple clouds, you can learn more in [Work with multiple clouds](https://docs.microsoft.com/cli/azure/manage-clouds-azure-cli?view=azure-cli-latest).

## Set CA bundle certificate
Please follow the first solution in [Work behind a proxy](https://docs.microsoft.com/cli/azure/use-cli-effectively?view=azure-cli-latest#work-behind-a-proxy) to set up the certificate in your airgapped cloud environment.

## Login with service principal
Use the service principal that was granted permission to access a subscription in the airgapped cloud to login.
```
az login --service-principal -u <service principal id> -p <service principal password> --tenant <tenant id>
```

## Run CLI Commands
If you meet any issues while running Azure CLI commands in airgapped clouds, please feedback through [Github issues](https://github.com/Azure/azure-cli/issues/new?assignees=&labels=&template=Bug_report.md&title=).
