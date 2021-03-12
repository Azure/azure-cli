# Azure CLI Module Creation Report

## EXTENSION
|CLI Extension|Command Groups|
|---------|------------|
|az vm|[groups](#CommandGroups)

## GROUPS
### <a name="CommandGroups">Command groups in `az vm` extension </a>
|CLI Command Group|Group Swagger name|Commands|
|---------|------------|--------|
|az vm ssh-public-key|SshPublicKeys|[commands](#CommandsInSshPublicKeys)|
|az vm virtual-machine|VirtualMachines|[commands](#CommandsInVirtualMachines)|
|az vm virtual-machine-scale-set|VirtualMachineScaleSets|[commands](#CommandsInVirtualMachineScaleSets)|
|az vm virtual-machine-scale-set-vm-extension|VirtualMachineScaleSetVMExtensions|[commands](#CommandsInVirtualMachineScaleSetVMExtensions)|
|az vm virtual-machine-scale-set-v-ms|VirtualMachineScaleSetVMs|[commands](#CommandsInVirtualMachineScaleSetVMs)|
|az vm virtual-machine-scale-set-vm-run-command|VirtualMachineScaleSetVMRunCommands|[commands](#CommandsInVirtualMachineScaleSetVMRunCommands)|
|az vm disk-access|DiskAccesses|[commands](#CommandsInDiskAccesses)|
|az vm gallery-application|GalleryApplications|[commands](#CommandsInGalleryApplications)|
|az vm gallery-application-version|GalleryApplicationVersions|[commands](#CommandsInGalleryApplicationVersions)|

## COMMANDS
### <a name="CommandsInDiskAccesses">Commands in `az vm disk-access` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm disk-access delete-a-private-endpoint-connection](#DiskAccessesDeleteAPrivateEndpointConnection)|DeleteAPrivateEndpointConnection|[Parameters](#ParametersDiskAccessesDeleteAPrivateEndpointConnection)|[Example](#ExamplesDiskAccessesDeleteAPrivateEndpointConnection)|
|[az vm disk-access show-private-link-resource](#DiskAccessesGetPrivateLinkResources)|GetPrivateLinkResources|[Parameters](#ParametersDiskAccessesGetPrivateLinkResources)|[Example](#ExamplesDiskAccessesGetPrivateLinkResources)|

### <a name="CommandsInGalleryApplications">Commands in `az vm gallery-application` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm gallery-application list](#GalleryApplicationsListByGallery)|ListByGallery|[Parameters](#ParametersGalleryApplicationsListByGallery)|[Example](#ExamplesGalleryApplicationsListByGallery)|
|[az vm gallery-application show](#GalleryApplicationsGet)|Get|[Parameters](#ParametersGalleryApplicationsGet)|[Example](#ExamplesGalleryApplicationsGet)|
|[az vm gallery-application create](#GalleryApplicationsCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersGalleryApplicationsCreateOrUpdate#Create)|[Example](#ExamplesGalleryApplicationsCreateOrUpdate#Create)|
|[az vm gallery-application delete](#GalleryApplicationsDelete)|Delete|[Parameters](#ParametersGalleryApplicationsDelete)|[Example](#ExamplesGalleryApplicationsDelete)|

### <a name="CommandsInGalleryApplicationVersions">Commands in `az vm gallery-application-version` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm gallery-application-version list](#GalleryApplicationVersionsListByGalleryApplication)|ListByGalleryApplication|[Parameters](#ParametersGalleryApplicationVersionsListByGalleryApplication)|[Example](#ExamplesGalleryApplicationVersionsListByGalleryApplication)|

### <a name="CommandsInSshPublicKeys">Commands in `az vm ssh-public-key` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm ssh-public-key list](#SshPublicKeysListByResourceGroup)|ListByResourceGroup|[Parameters](#ParametersSshPublicKeysListByResourceGroup)|Not Found|
|[az vm ssh-public-key list](#SshPublicKeysListBySubscription)|ListBySubscription|[Parameters](#ParametersSshPublicKeysListBySubscription)|Not Found|
|[az vm ssh-public-key show](#SshPublicKeysGet)|Get|[Parameters](#ParametersSshPublicKeysGet)|[Example](#ExamplesSshPublicKeysGet)|
|[az vm ssh-public-key create](#SshPublicKeysCreate)|Create|[Parameters](#ParametersSshPublicKeysCreate)|[Example](#ExamplesSshPublicKeysCreate)|
|[az vm ssh-public-key update](#SshPublicKeysUpdate)|Update|[Parameters](#ParametersSshPublicKeysUpdate)|Not Found|
|[az vm ssh-public-key delete](#SshPublicKeysDelete)|Delete|[Parameters](#ParametersSshPublicKeysDelete)|Not Found|
|[az vm ssh-public-key generate-key-pair](#SshPublicKeysGenerateKeyPair)|GenerateKeyPair|[Parameters](#ParametersSshPublicKeysGenerateKeyPair)|[Example](#ExamplesSshPublicKeysGenerateKeyPair)|

### <a name="CommandsInVirtualMachines">Commands in `az vm virtual-machine` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm virtual-machine reimage](#VirtualMachinesReimage)|Reimage|[Parameters](#ParametersVirtualMachinesReimage)|[Example](#ExamplesVirtualMachinesReimage)|

### <a name="CommandsInVirtualMachineScaleSets">Commands in `az vm virtual-machine-scale-set` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm virtual-machine-scale-set force-recovery-service-fabric-platform-update-domain-walk](#VirtualMachineScaleSetsForceRecoveryServiceFabricPlatformUpdateDomainWalk)|ForceRecoveryServiceFabricPlatformUpdateDomainWalk|[Parameters](#ParametersVirtualMachineScaleSetsForceRecoveryServiceFabricPlatformUpdateDomainWalk)|Not Found|
|[az vm virtual-machine-scale-set redeploy](#VirtualMachineScaleSetsRedeploy)|Redeploy|[Parameters](#ParametersVirtualMachineScaleSetsRedeploy)|Not Found|
|[az vm virtual-machine-scale-set reimage-all](#VirtualMachineScaleSetsReimageAll)|ReimageAll|[Parameters](#ParametersVirtualMachineScaleSetsReimageAll)|Not Found|

### <a name="CommandsInVirtualMachineScaleSetVMs">Commands in `az vm virtual-machine-scale-set-v-ms` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm virtual-machine-scale-set-v-ms redeploy](#VirtualMachineScaleSetVMsRedeploy)|Redeploy|[Parameters](#ParametersVirtualMachineScaleSetVMsRedeploy)|Not Found|
|[az vm virtual-machine-scale-set-v-ms reimage-all](#VirtualMachineScaleSetVMsReimageAll)|ReimageAll|[Parameters](#ParametersVirtualMachineScaleSetVMsReimageAll)|Not Found|
|[az vm virtual-machine-scale-set-v-ms retrieve-boot-diagnostic-data](#VirtualMachineScaleSetVMsRetrieveBootDiagnosticsData)|RetrieveBootDiagnosticsData|[Parameters](#ParametersVirtualMachineScaleSetVMsRetrieveBootDiagnosticsData)|[Example](#ExamplesVirtualMachineScaleSetVMsRetrieveBootDiagnosticsData)|

### <a name="CommandsInVirtualMachineScaleSetVMExtensions">Commands in `az vm virtual-machine-scale-set-vm-extension` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm virtual-machine-scale-set-vm-extension list](#VirtualMachineScaleSetVMExtensionsList)|List|[Parameters](#ParametersVirtualMachineScaleSetVMExtensionsList)|[Example](#ExamplesVirtualMachineScaleSetVMExtensionsList)|
|[az vm virtual-machine-scale-set-vm-extension show](#VirtualMachineScaleSetVMExtensionsGet)|Get|[Parameters](#ParametersVirtualMachineScaleSetVMExtensionsGet)|[Example](#ExamplesVirtualMachineScaleSetVMExtensionsGet)|
|[az vm virtual-machine-scale-set-vm-extension create](#VirtualMachineScaleSetVMExtensionsCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersVirtualMachineScaleSetVMExtensionsCreateOrUpdate#Create)|[Example](#ExamplesVirtualMachineScaleSetVMExtensionsCreateOrUpdate#Create)|

### <a name="CommandsInVirtualMachineScaleSetVMRunCommands">Commands in `az vm virtual-machine-scale-set-vm-run-command` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm virtual-machine-scale-set-vm-run-command list](#VirtualMachineScaleSetVMRunCommandsList)|List|[Parameters](#ParametersVirtualMachineScaleSetVMRunCommandsList)|[Example](#ExamplesVirtualMachineScaleSetVMRunCommandsList)|


## COMMAND DETAILS

### group `az vm disk-access`
#### <a name="DiskAccessesDeleteAPrivateEndpointConnection">Command `az vm disk-access delete-a-private-endpoint-connection`</a>

##### <a name="ExamplesDiskAccessesDeleteAPrivateEndpointConnection">Example</a>
```
az vm disk-access delete-a-private-endpoint-connection --name "myDiskAccess" --private-endpoint-connection-name \
"myPrivateEndpointConnection" --resource-group "myResourceGroup"
```
##### <a name="ParametersDiskAccessesDeleteAPrivateEndpointConnection">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--disk-access-name**|string|The name of the disk access resource that is being created. The name can't be changed after the disk encryption set is created. Supported characters for the name are a-z, A-Z, 0-9 and _. The maximum name length is 80 characters.|disk_access_name|diskAccessName|
|**--private-endpoint-connection-name**|string|The name of the private endpoint connection|private_endpoint_connection_name|privateEndpointConnectionName|

#### <a name="DiskAccessesGetPrivateLinkResources">Command `az vm disk-access show-private-link-resource`</a>

##### <a name="ExamplesDiskAccessesGetPrivateLinkResources">Example</a>
```
az vm disk-access show-private-link-resource --name "myDiskAccess" --resource-group "myResourceGroup"
```
##### <a name="ParametersDiskAccessesGetPrivateLinkResources">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--disk-access-name**|string|The name of the disk access resource that is being created. The name can't be changed after the disk encryption set is created. Supported characters for the name are a-z, A-Z, 0-9 and _. The maximum name length is 80 characters.|disk_access_name|diskAccessName|

### group `az vm gallery-application`
#### <a name="GalleryApplicationsListByGallery">Command `az vm gallery-application list`</a>

##### <a name="ExamplesGalleryApplicationsListByGallery">Example</a>
```
az vm gallery-application list --gallery-name "myGalleryName" --resource-group "myResourceGroup"
```
##### <a name="ParametersGalleryApplicationsListByGallery">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--gallery-name**|string|The name of the Shared Application Gallery from which Application Definitions are to be listed.|gallery_name|galleryName|

#### <a name="GalleryApplicationsGet">Command `az vm gallery-application show`</a>

##### <a name="ExamplesGalleryApplicationsGet">Example</a>
```
az vm gallery-application show --name "myGalleryApplicationName" --gallery-name "myGalleryName" --resource-group \
"myResourceGroup"
```
##### <a name="ParametersGalleryApplicationsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--gallery-name**|string|The name of the Shared Application Gallery from which the Application Definitions are to be retrieved.|gallery_name|galleryName|
|**--gallery-application-name**|string|The name of the gallery Application Definition to be retrieved.|gallery_application_name|galleryApplicationName|

#### <a name="GalleryApplicationsCreateOrUpdate#Create">Command `az vm gallery-application create`</a>

##### <a name="ExamplesGalleryApplicationsCreateOrUpdate#Create">Example</a>
```
az vm gallery-application create --location "West US" --description "This is the gallery application description." \
--eula "This is the gallery application EULA." --privacy-statement-uri "myPrivacyStatementUri}" --release-note-uri \
"myReleaseNoteUri" --supported-os-type "Windows" --name "myGalleryApplicationName" --gallery-name "myGalleryName" \
--resource-group "myResourceGroup"
```
##### <a name="ParametersGalleryApplicationsCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--gallery-name**|string|The name of the Shared Application Gallery in which the Application Definition is to be created.|gallery_name|galleryName|
|**--gallery-application-name**|string|The name of the gallery Application Definition to be created or updated. The allowed characters are alphabets and numbers with dots, dashes, and periods allowed in the middle. The maximum length is 80 characters.|gallery_application_name|galleryApplicationName|
|**--location**|string|Resource location|location|location|
|**--tags**|dictionary|Resource tags|tags|tags|
|**--description**|string|The description of this gallery Application Definition resource. This property is updatable.|description|description|
|**--eula**|string|The Eula agreement for the gallery Application Definition.|eula|eula|
|**--privacy-statement-uri**|string|The privacy statement uri.|privacy_statement_uri|privacyStatementUri|
|**--release-note-uri**|string|The release note uri.|release_note_uri|releaseNoteUri|
|**--end-of-life-date**|date-time|The end of life date of the gallery Application Definition. This property can be used for decommissioning purposes. This property is updatable.|end_of_life_date|endOfLifeDate|
|**--supported-os-type**|sealed-choice|This property allows you to specify the supported type of the OS that application is built for. <br><br> Possible values are: <br><br> **Windows** <br><br> **Linux**|supported_os_type|supportedOSType|

#### <a name="GalleryApplicationsDelete">Command `az vm gallery-application delete`</a>

##### <a name="ExamplesGalleryApplicationsDelete">Example</a>
```
az vm gallery-application delete --name "myGalleryApplicationName" --gallery-name "myGalleryName" --resource-group \
"myResourceGroup"
```
##### <a name="ParametersGalleryApplicationsDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--gallery-name**|string|The name of the Shared Application Gallery in which the Application Definition is to be deleted.|gallery_name|galleryName|
|**--gallery-application-name**|string|The name of the gallery Application Definition to be deleted.|gallery_application_name|galleryApplicationName|

### group `az vm gallery-application-version`
#### <a name="GalleryApplicationVersionsListByGalleryApplication">Command `az vm gallery-application-version list`</a>

##### <a name="ExamplesGalleryApplicationVersionsListByGalleryApplication">Example</a>
```
az vm gallery-application-version list --gallery-application-name "myGalleryApplicationName" --gallery-name \
"myGalleryName" --resource-group "myResourceGroup"
```
##### <a name="ParametersGalleryApplicationVersionsListByGalleryApplication">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--gallery-name**|string|The name of the Shared Application Gallery in which the Application Definition resides.|gallery_name|galleryName|
|**--gallery-application-name**|string|The name of the Shared Application Gallery Application Definition from which the Application Versions are to be listed.|gallery_application_name|galleryApplicationName|

### group `az vm ssh-public-key`
#### <a name="SshPublicKeysListByResourceGroup">Command `az vm ssh-public-key list`</a>

##### <a name="ParametersSshPublicKeysListByResourceGroup">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|

#### <a name="SshPublicKeysListBySubscription">Command `az vm ssh-public-key list`</a>

##### <a name="ParametersSshPublicKeysListBySubscription">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="SshPublicKeysGet">Command `az vm ssh-public-key show`</a>

##### <a name="ExamplesSshPublicKeysGet">Example</a>
```
az vm ssh-public-key show --resource-group "myResourceGroup" --name "mySshPublicKeyName"
```
##### <a name="ParametersSshPublicKeysGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--ssh-public-key-name**|string|The name of the SSH public key.|ssh_public_key_name|sshPublicKeyName|

#### <a name="SshPublicKeysCreate">Command `az vm ssh-public-key create`</a>

##### <a name="ExamplesSshPublicKeysCreate">Example</a>
```
az vm ssh-public-key create --location "westus" --public-key "{ssh-rsa public key}" --resource-group "myResourceGroup" \
--name "mySshPublicKeyName"
```
##### <a name="ParametersSshPublicKeysCreate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--ssh-public-key-name**|string|The name of the SSH public key.|ssh_public_key_name|sshPublicKeyName|
|**--location**|string|Resource location|location|location|
|**--tags**|dictionary|Resource tags|tags|tags|
|**--public-key**|string|SSH public key used to authenticate to a virtual machine through ssh. If this property is not initially provided when the resource is created, the publicKey property will be populated when generateKeyPair is called. If the public key is provided upon resource creation, the provided public key needs to be at least 2048-bit and in ssh-rsa format.|public_key|publicKey|

#### <a name="SshPublicKeysUpdate">Command `az vm ssh-public-key update`</a>

##### <a name="ParametersSshPublicKeysUpdate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--ssh-public-key-name**|string|The name of the SSH public key.|ssh_public_key_name|sshPublicKeyName|
|**--tags**|dictionary|Resource tags|tags|tags|
|**--public-key**|string|SSH public key used to authenticate to a virtual machine through ssh. If this property is not initially provided when the resource is created, the publicKey property will be populated when generateKeyPair is called. If the public key is provided upon resource creation, the provided public key needs to be at least 2048-bit and in ssh-rsa format.|public_key|publicKey|

#### <a name="SshPublicKeysDelete">Command `az vm ssh-public-key delete`</a>

##### <a name="ParametersSshPublicKeysDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--ssh-public-key-name**|string|The name of the SSH public key.|ssh_public_key_name|sshPublicKeyName|

#### <a name="SshPublicKeysGenerateKeyPair">Command `az vm ssh-public-key generate-key-pair`</a>

##### <a name="ExamplesSshPublicKeysGenerateKeyPair">Example</a>
```
az vm ssh-public-key generate-key-pair --resource-group "myResourceGroup" --name "mySshPublicKeyName"
```
##### <a name="ParametersSshPublicKeysGenerateKeyPair">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--ssh-public-key-name**|string|The name of the SSH public key.|ssh_public_key_name|sshPublicKeyName|

### group `az vm virtual-machine`
#### <a name="VirtualMachinesReimage">Command `az vm virtual-machine reimage`</a>

##### <a name="ExamplesVirtualMachinesReimage">Example</a>
```
az vm virtual-machine reimage --temp-disk true --resource-group "myResourceGroup" --vm-name "myVMName"
```
##### <a name="ParametersVirtualMachinesReimage">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-name**|string|The name of the virtual machine.|vm_name|vmName|
|**--temp-disk**|boolean|Specifies whether to reimage temp disk. Default value: false. Note: This temp disk reimage parameter is only supported for VM/VMSS with Ephemeral OS disk.|temp_disk|tempDisk|

### group `az vm virtual-machine-scale-set`
#### <a name="VirtualMachineScaleSetsForceRecoveryServiceFabricPlatformUpdateDomainWalk">Command `az vm virtual-machine-scale-set force-recovery-service-fabric-platform-update-domain-walk`</a>

##### <a name="ParametersVirtualMachineScaleSetsForceRecoveryServiceFabricPlatformUpdateDomainWalk">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--platform-update-domain**|integer|The platform update domain for which a manual recovery walk is requested|platform_update_domain|platformUpdateDomain|

#### <a name="VirtualMachineScaleSetsRedeploy">Command `az vm virtual-machine-scale-set redeploy`</a>

##### <a name="ParametersVirtualMachineScaleSetsRedeploy">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--instance-ids**|array|The virtual machine scale set instance ids. Omitting the virtual machine scale set instance ids will result in the operation being performed on all virtual machines in the virtual machine scale set.|instance_ids|instanceIds|

#### <a name="VirtualMachineScaleSetsReimageAll">Command `az vm virtual-machine-scale-set reimage-all`</a>

##### <a name="ParametersVirtualMachineScaleSetsReimageAll">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--instance-ids**|array|The virtual machine scale set instance ids. Omitting the virtual machine scale set instance ids will result in the operation being performed on all virtual machines in the virtual machine scale set.|instance_ids|instanceIds|

### group `az vm virtual-machine-scale-set-v-ms`
#### <a name="VirtualMachineScaleSetVMsRedeploy">Command `az vm virtual-machine-scale-set-v-ms redeploy`</a>

##### <a name="ParametersVirtualMachineScaleSetVMsRedeploy">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--instance-id**|string|The instance ID of the virtual machine.|instance_id|instanceId|

#### <a name="VirtualMachineScaleSetVMsReimageAll">Command `az vm virtual-machine-scale-set-v-ms reimage-all`</a>

##### <a name="ParametersVirtualMachineScaleSetVMsReimageAll">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--instance-id**|string|The instance ID of the virtual machine.|instance_id|instanceId|

#### <a name="VirtualMachineScaleSetVMsRetrieveBootDiagnosticsData">Command `az vm virtual-machine-scale-set-v-ms retrieve-boot-diagnostic-data`</a>

##### <a name="ExamplesVirtualMachineScaleSetVMsRetrieveBootDiagnosticsData">Example</a>
```
az vm virtual-machine-scale-set-v-ms retrieve-boot-diagnostic-data --instance-id "0" --resource-group "ResourceGroup" \
--sas-uri-expiration-time-in-minutes 60 --vm-scale-set-name "myvmScaleSet"
```
##### <a name="ParametersVirtualMachineScaleSetVMsRetrieveBootDiagnosticsData">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--instance-id**|string|The instance ID of the virtual machine.|instance_id|instanceId|
|**--sas-uri-expiration-time-in-minutes**|integer|Expiration duration in minutes for the SAS URIs with a value between 1 to 1440 minutes. <br><br>NOTE: If not specified, SAS URIs will be generated with a default expiration duration of 120 minutes.|sas_uri_expiration_time_in_minutes|sasUriExpirationTimeInMinutes|

### group `az vm virtual-machine-scale-set-vm-extension`
#### <a name="VirtualMachineScaleSetVMExtensionsList">Command `az vm virtual-machine-scale-set-vm-extension list`</a>

##### <a name="ExamplesVirtualMachineScaleSetVMExtensionsList">Example</a>
```
az vm virtual-machine-scale-set-vm-extension list --instance-id "0" --resource-group "myResourceGroup" \
--vm-scale-set-name "myvmScaleSet"
```
##### <a name="ParametersVirtualMachineScaleSetVMExtensionsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--instance-id**|string|The instance ID of the virtual machine.|instance_id|instanceId|
|**--expand**|string|The expand expression to apply on the operation.|expand|$expand|

#### <a name="VirtualMachineScaleSetVMExtensionsGet">Command `az vm virtual-machine-scale-set-vm-extension show`</a>

##### <a name="ExamplesVirtualMachineScaleSetVMExtensionsGet">Example</a>
```
az vm virtual-machine-scale-set-vm-extension show --instance-id "0" --resource-group "myResourceGroup" \
--vm-extension-name "myVMExtension" --vm-scale-set-name "myvmScaleSet"
```
##### <a name="ParametersVirtualMachineScaleSetVMExtensionsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--instance-id**|string|The instance ID of the virtual machine.|instance_id|instanceId|
|**--vm-extension-name**|string|The name of the virtual machine extension.|vm_extension_name|vmExtensionName|
|**--expand**|string|The expand expression to apply on the operation.|expand|$expand|

#### <a name="VirtualMachineScaleSetVMExtensionsCreateOrUpdate#Create">Command `az vm virtual-machine-scale-set-vm-extension create`</a>

##### <a name="ExamplesVirtualMachineScaleSetVMExtensionsCreateOrUpdate#Create">Example</a>
```
az vm virtual-machine-scale-set-vm-extension create --type-properties-type "extType" --auto-upgrade-minor-version true \
--publisher "extPublisher" --settings "{\\"UserName\\":\\"xyz@microsoft.com\\"}" --type-handler-version "1.2" \
--instance-id "0" --resource-group "myResourceGroup" --vm-extension-name "myVMExtension" --vm-scale-set-name \
"myvmScaleSet"
```
##### <a name="ParametersVirtualMachineScaleSetVMExtensionsCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--instance-id**|string|The instance ID of the virtual machine.|instance_id|instanceId|
|**--vm-extension-name**|string|The name of the virtual machine extension.|vm_extension_name|vmExtensionName|
|**--force-update-tag**|string|How the extension handler should be forced to update even if the extension configuration has not changed.|force_update_tag|forceUpdateTag|
|**--publisher**|string|The name of the extension handler publisher.|publisher|publisher|
|**--type-properties-type**|string|Specifies the type of the extension; an example is "CustomScriptExtension".|type_properties_type|type|
|**--type-handler-version**|string|Specifies the version of the script handler.|type_handler_version|typeHandlerVersion|
|**--auto-upgrade-minor-version**|boolean|Indicates whether the extension should use a newer minor version if one is available at deployment time. Once deployed, however, the extension will not upgrade minor versions unless redeployed, even with this property set to true.|auto_upgrade_minor_version|autoUpgradeMinorVersion|
|**--enable-automatic-upgrade**|boolean|Indicates whether the extension should be automatically upgraded by the platform if there is a newer version of the extension available.|enable_automatic_upgrade|enableAutomaticUpgrade|
|**--settings**|any|Json formatted public settings for the extension.|settings|settings|
|**--protected-settings**|any|The extension can contain either protectedSettings or protectedSettingsFromKeyVault or no protected settings at all.|protected_settings|protectedSettings|
|**--name**|string|The virtual machine extension name.|name|name|
|**--type**|string|Specifies the type of the extension; an example is "CustomScriptExtension".|type|type|
|**--virtual-machine-extension-instance-view-type-handler-version-type-handler-version**|string|Specifies the version of the script handler.|virtual_machine_extension_instance_view_type_handler_version_type_handler_version|typeHandlerVersion|
|**--substatuses**|array|The resource status information.|substatuses|substatuses|
|**--statuses**|array|The resource status information.|statuses|statuses|

### group `az vm virtual-machine-scale-set-vm-run-command`
#### <a name="VirtualMachineScaleSetVMRunCommandsList">Command `az vm virtual-machine-scale-set-vm-run-command list`</a>

##### <a name="ExamplesVirtualMachineScaleSetVMRunCommandsList">Example</a>
```
az vm virtual-machine-scale-set-vm-run-command list --instance-id "0" --resource-group "myResourceGroup" \
--vm-scale-set-name "myvmScaleSet"
```
##### <a name="ParametersVirtualMachineScaleSetVMRunCommandsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-scale-set-name**|string|The name of the VM scale set.|vm_scale_set_name|vmScaleSetName|
|**--instance-id**|string|The instance ID of the virtual machine.|instance_id|instanceId|
|**--expand**|string|The expand expression to apply on the operation.|expand|$expand|
