# Azure CLI Module Creation Report

## EXTENSION
|CLI Extension|Command Groups|
|---------|------------|
|az vm|[groups](#CommandGroups)

## GROUPS
### <a name="CommandGroups">Command groups in `az vm` extension </a>
|CLI Command Group|Group Swagger name|Commands|
|---------|------------|--------|
|az sshkey|SshPublicKeys|[commands](#CommandsInSshPublicKeys)|
|az vm virtual-machine|VirtualMachines|[commands](#CommandsInVirtualMachines)|
|az vm virtual-machine-scale-set|VirtualMachineScaleSets|[commands](#CommandsInVirtualMachineScaleSets)|
|az vm virtual-machine-scale-set-vm-extension|VirtualMachineScaleSetVMExtensions|[commands](#CommandsInVirtualMachineScaleSetVMExtensions)|
|az vm virtual-machine-scale-set-v-ms|VirtualMachineScaleSetVMs|[commands](#CommandsInVirtualMachineScaleSetVMs)|
|az vm virtual-machine-scale-set-vm-run-command|VirtualMachineScaleSetVMRunCommands|[commands](#CommandsInVirtualMachineScaleSetVMRunCommands)|
|az vm disk-access|DiskAccesses|[commands](#CommandsInDiskAccesses)|
|az vm disk-restore-point|DiskRestorePoint|[commands](#CommandsInDiskRestorePoint)|
|az vm gallery-application|GalleryApplications|[commands](#CommandsInGalleryApplications)|
|az vm gallery-application-version|GalleryApplicationVersions|[commands](#CommandsInGalleryApplicationVersions)|
|az vm cloud-service-role-instance|CloudServiceRoleInstances|[commands](#CommandsInCloudServiceRoleInstances)|
|az vm cloud-service-role|CloudServiceRoles|[commands](#CommandsInCloudServiceRoles)|
|az vm cloud-service|CloudServices|[commands](#CommandsInCloudServices)|
|az vm cloud-service-update-domain|CloudServicesUpdateDomain|[commands](#CommandsInCloudServicesUpdateDomain)|

## COMMANDS
### <a name="CommandsInSshPublicKeys">Commands in `az sshkey` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az sshkey list](#SshPublicKeysListByResourceGroup)|ListByResourceGroup|[Parameters](#ParametersSshPublicKeysListByResourceGroup)|Not Found|
|[az sshkey list](#SshPublicKeysListBySubscription)|ListBySubscription|[Parameters](#ParametersSshPublicKeysListBySubscription)|Not Found|
|[az sshkey show](#SshPublicKeysGet)|Get|[Parameters](#ParametersSshPublicKeysGet)|[Example](#ExamplesSshPublicKeysGet)|
|[az sshkey create](#SshPublicKeysCreate)|Create|[Parameters](#ParametersSshPublicKeysCreate)|[Example](#ExamplesSshPublicKeysCreate)|
|[az sshkey update](#SshPublicKeysUpdate)|Update|[Parameters](#ParametersSshPublicKeysUpdate)|Not Found|
|[az sshkey delete](#SshPublicKeysDelete)|Delete|[Parameters](#ParametersSshPublicKeysDelete)|Not Found|

### <a name="CommandsInCloudServices">Commands in `az vm cloud-service` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm cloud-service list](#CloudServicesList)|List|[Parameters](#ParametersCloudServicesList)|[Example](#ExamplesCloudServicesList)|
|[az vm cloud-service show](#CloudServicesGet)|Get|[Parameters](#ParametersCloudServicesGet)|[Example](#ExamplesCloudServicesGet)|
|[az vm cloud-service create](#CloudServicesCreateOrUpdate#Create)|CreateOrUpdate#Create|[Parameters](#ParametersCloudServicesCreateOrUpdate#Create)|[Example](#ExamplesCloudServicesCreateOrUpdate#Create)|
|[az vm cloud-service delete](#CloudServicesDelete)|Delete|[Parameters](#ParametersCloudServicesDelete)|[Example](#ExamplesCloudServicesDelete)|
|[az vm cloud-service delete-instance](#CloudServicesDeleteInstances)|DeleteInstances|[Parameters](#ParametersCloudServicesDeleteInstances)|[Example](#ExamplesCloudServicesDeleteInstances)|
|[az vm cloud-service list-all](#CloudServicesListAll)|ListAll|[Parameters](#ParametersCloudServicesListAll)|[Example](#ExamplesCloudServicesListAll)|
|[az vm cloud-service power-off](#CloudServicesPowerOff)|PowerOff|[Parameters](#ParametersCloudServicesPowerOff)|[Example](#ExamplesCloudServicesPowerOff)|
|[az vm cloud-service restart](#CloudServicesRestart)|Restart|[Parameters](#ParametersCloudServicesRestart)|[Example](#ExamplesCloudServicesRestart)|
|[az vm cloud-service show-instance-view](#CloudServicesGetInstanceView)|GetInstanceView|[Parameters](#ParametersCloudServicesGetInstanceView)|[Example](#ExamplesCloudServicesGetInstanceView)|
|[az vm cloud-service start](#CloudServicesStart)|Start|[Parameters](#ParametersCloudServicesStart)|[Example](#ExamplesCloudServicesStart)|

### <a name="CommandsInCloudServiceRoles">Commands in `az vm cloud-service-role` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm cloud-service-role list](#CloudServiceRolesList)|List|[Parameters](#ParametersCloudServiceRolesList)|[Example](#ExamplesCloudServiceRolesList)|
|[az vm cloud-service-role show](#CloudServiceRolesGet)|Get|[Parameters](#ParametersCloudServiceRolesGet)|[Example](#ExamplesCloudServiceRolesGet)|

### <a name="CommandsInCloudServiceRoleInstances">Commands in `az vm cloud-service-role-instance` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm cloud-service-role-instance list](#CloudServiceRoleInstancesList)|List|[Parameters](#ParametersCloudServiceRoleInstancesList)|[Example](#ExamplesCloudServiceRoleInstancesList)|
|[az vm cloud-service-role-instance show](#CloudServiceRoleInstancesGet)|Get|[Parameters](#ParametersCloudServiceRoleInstancesGet)|[Example](#ExamplesCloudServiceRoleInstancesGet)|
|[az vm cloud-service-role-instance reimage](#CloudServiceRoleInstancesReimage)|Reimage|[Parameters](#ParametersCloudServiceRoleInstancesReimage)|[Example](#ExamplesCloudServiceRoleInstancesReimage)|
|[az vm cloud-service-role-instance restart](#CloudServiceRoleInstancesRestart)|Restart|[Parameters](#ParametersCloudServiceRoleInstancesRestart)|[Example](#ExamplesCloudServiceRoleInstancesRestart)|
|[az vm cloud-service-role-instance show-instance-view](#CloudServiceRoleInstancesGetInstanceView)|GetInstanceView|[Parameters](#ParametersCloudServiceRoleInstancesGetInstanceView)|[Example](#ExamplesCloudServiceRoleInstancesGetInstanceView)|
|[az vm cloud-service-role-instance show-remote-desktop-file](#CloudServiceRoleInstancesGetRemoteDesktopFile)|GetRemoteDesktopFile|[Parameters](#ParametersCloudServiceRoleInstancesGetRemoteDesktopFile)|Not Found|

### <a name="CommandsInCloudServicesUpdateDomain">Commands in `az vm cloud-service-update-domain` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm cloud-service-update-domain list-update-domain](#CloudServicesUpdateDomainListUpdateDomains)|ListUpdateDomains|[Parameters](#ParametersCloudServicesUpdateDomainListUpdateDomains)|[Example](#ExamplesCloudServicesUpdateDomainListUpdateDomains)|
|[az vm cloud-service-update-domain show-update-domain](#CloudServicesUpdateDomainGetUpdateDomain)|GetUpdateDomain|[Parameters](#ParametersCloudServicesUpdateDomainGetUpdateDomain)|[Example](#ExamplesCloudServicesUpdateDomainGetUpdateDomain)|
|[az vm cloud-service-update-domain walk-update-domain](#CloudServicesUpdateDomainWalkUpdateDomain)|WalkUpdateDomain|[Parameters](#ParametersCloudServicesUpdateDomainWalkUpdateDomain)|[Example](#ExamplesCloudServicesUpdateDomainWalkUpdateDomain)|

### <a name="CommandsInDiskAccesses">Commands in `az vm disk-access` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm disk-access delete-a-private-endpoint-connection](#DiskAccessesDeleteAPrivateEndpointConnection)|DeleteAPrivateEndpointConnection|[Parameters](#ParametersDiskAccessesDeleteAPrivateEndpointConnection)|[Example](#ExamplesDiskAccessesDeleteAPrivateEndpointConnection)|
|[az vm disk-access list-private-endpoint-connection](#DiskAccessesListPrivateEndpointConnections)|ListPrivateEndpointConnections|[Parameters](#ParametersDiskAccessesListPrivateEndpointConnections)|[Example](#ExamplesDiskAccessesListPrivateEndpointConnections)|
|[az vm disk-access show-private-link-resource](#DiskAccessesGetPrivateLinkResources)|GetPrivateLinkResources|[Parameters](#ParametersDiskAccessesGetPrivateLinkResources)|[Example](#ExamplesDiskAccessesGetPrivateLinkResources)|

### <a name="CommandsInDiskRestorePoint">Commands in `az vm disk-restore-point` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm disk-restore-point show](#DiskRestorePointGet)|Get|[Parameters](#ParametersDiskRestorePointGet)|[Example](#ExamplesDiskRestorePointGet)|

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

### <a name="CommandsInVirtualMachines">Commands in `az vm virtual-machine` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az vm virtual-machine install-patch](#VirtualMachinesInstallPatches)|InstallPatches|[Parameters](#ParametersVirtualMachinesInstallPatches)|[Example](#ExamplesVirtualMachinesInstallPatches)|
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

### group `az sshkey`
#### <a name="SshPublicKeysListByResourceGroup">Command `az sshkey list`</a>

##### <a name="ParametersSshPublicKeysListByResourceGroup">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|

#### <a name="SshPublicKeysListBySubscription">Command `az sshkey list`</a>

##### <a name="ParametersSshPublicKeysListBySubscription">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="SshPublicKeysGet">Command `az sshkey show`</a>

##### <a name="ExamplesSshPublicKeysGet">Example</a>
```
az sshkey show --resource-group "myResourceGroup" --name "mySshPublicKeyName"
```
##### <a name="ParametersSshPublicKeysGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--ssh-public-key-name**|string|The name of the SSH public key.|ssh_public_key_name|sshPublicKeyName|

#### <a name="SshPublicKeysCreate">Command `az sshkey create`</a>

##### <a name="ExamplesSshPublicKeysCreate">Example</a>
```
az sshkey create --location "westus" --public-key "{ssh-rsa public key}" --resource-group "myResourceGroup" --name \
"mySshPublicKeyName"
```
##### <a name="ParametersSshPublicKeysCreate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--ssh-public-key-name**|string|The name of the SSH public key.|ssh_public_key_name|sshPublicKeyName|
|**--location**|string|Resource location|location|location|
|**--tags**|dictionary|Resource tags|tags|tags|
|**--public-key**|string|SSH public key used to authenticate to a virtual machine through ssh. If this property is not initially provided when the resource is created, the publicKey property will be populated when generateKeyPair is called. If the public key is provided upon resource creation, the provided public key needs to be at least 2048-bit and in ssh-rsa format.|public_key|publicKey|

#### <a name="SshPublicKeysUpdate">Command `az sshkey update`</a>

##### <a name="ParametersSshPublicKeysUpdate">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--ssh-public-key-name**|string|The name of the SSH public key.|ssh_public_key_name|sshPublicKeyName|
|**--tags**|dictionary|Resource tags|tags|tags|
|**--public-key**|string|SSH public key used to authenticate to a virtual machine through ssh. If this property is not initially provided when the resource is created, the publicKey property will be populated when generateKeyPair is called. If the public key is provided upon resource creation, the provided public key needs to be at least 2048-bit and in ssh-rsa format.|public_key|publicKey|

#### <a name="SshPublicKeysDelete">Command `az sshkey delete`</a>

##### <a name="ParametersSshPublicKeysDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--ssh-public-key-name**|string|The name of the SSH public key.|ssh_public_key_name|sshPublicKeyName|

### group `az vm cloud-service`
#### <a name="CloudServicesList">Command `az vm cloud-service list`</a>

##### <a name="ExamplesCloudServicesList">Example</a>
```
az vm cloud-service list --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|

#### <a name="CloudServicesGet">Command `az vm cloud-service show`</a>

##### <a name="ExamplesCloudServicesGet">Example</a>
```
az vm cloud-service show --name "{cs-name}" --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|

#### <a name="CloudServicesCreateOrUpdate#Create">Command `az vm cloud-service create`</a>

##### <a name="ExamplesCloudServicesCreateOrUpdate#Create">Example</a>
```
az vm cloud-service create --name "{cs-name}" --location "westus" --configuration "{ServiceConfiguration}" \
--load-balancer-configurations "[{\\"name\\":\\"contosolb\\",\\"properties\\":{\\"frontendIPConfigurations\\":[{\\"name\
\\":\\"contosofe\\",\\"properties\\":{\\"publicIPAddress\\":{\\"id\\":\\"/subscriptions/{subscription-id}/resourceGroup\
s/ConstosoRG/providers/Microsoft.Network/publicIPAddresses/contosopublicip\\"}}}]}}]" --package-url "{PackageUrl}" \
--roles "[{\\"name\\":\\"ContosoFrontend\\",\\"sku\\":{\\"name\\":\\"Standard_D1_v2\\",\\"capacity\\":1,\\"tier\\":\\"S\
tandard\\"}},{\\"name\\":\\"ContosoBackend\\",\\"sku\\":{\\"name\\":\\"Standard_D1_v2\\",\\"capacity\\":1,\\"tier\\":\\\
"Standard\\"}}]" --upgrade-mode "Auto" --resource-group "ConstosoRG"
```
##### <a name="ExamplesCloudServicesCreateOrUpdate#Create">Example</a>
```
az vm cloud-service create --name "{cs-name}" --location "westus" --configuration "{ServiceConfiguration}" \
--load-balancer-configurations "[{\\"name\\":\\"myLoadBalancer\\",\\"properties\\":{\\"frontendIPConfigurations\\":[{\\\
"name\\":\\"myfe\\",\\"properties\\":{\\"publicIPAddress\\":{\\"id\\":\\"/subscriptions/{subscription-id}/resourceGroup\
s/ConstosoRG/providers/Microsoft.Network/publicIPAddresses/myPublicIP\\"}}}]}}]" --package-url "{PackageUrl}" --roles \
"[{\\"name\\":\\"ContosoFrontend\\",\\"sku\\":{\\"name\\":\\"Standard_D1_v2\\",\\"capacity\\":1,\\"tier\\":\\"Standard\
\\"}}]" --upgrade-mode "Auto" --resource-group "ConstosoRG"
```
##### <a name="ExamplesCloudServicesCreateOrUpdate#Create">Example</a>
```
az vm cloud-service create --name "{cs-name}" --location "westus" --configuration "{ServiceConfiguration}" \
--load-balancer-configurations "[{\\"name\\":\\"contosolb\\",\\"properties\\":{\\"frontendIPConfigurations\\":[{\\"name\
\\":\\"contosofe\\",\\"properties\\":{\\"publicIPAddress\\":{\\"id\\":\\"/subscriptions/{subscription-id}/resourceGroup\
s/ConstosoRG/providers/Microsoft.Network/publicIPAddresses/contosopublicip\\"}}}]}}]" --secrets \
"[{\\"sourceVault\\":{\\"id\\":\\"/subscriptions/{subscription-id}/resourceGroups/ConstosoRG/providers/Microsoft.KeyVau\
lt/vaults/{keyvault-name}\\"},\\"vaultCertificates\\":[{\\"certificateUrl\\":\\"https://{keyvault-name}.vault.azure.net\
:443/secrets/ContosoCertificate/{secret-id}\\"}]}]" --package-url "{PackageUrl}" --roles \
"[{\\"name\\":\\"ContosoFrontend\\",\\"sku\\":{\\"name\\":\\"Standard_D1_v2\\",\\"capacity\\":1,\\"tier\\":\\"Standard\
\\"}}]" --upgrade-mode "Auto" --resource-group "ConstosoRG"
```
##### <a name="ExamplesCloudServicesCreateOrUpdate#Create">Example</a>
```
az vm cloud-service create --name "{cs-name}" --location "westus" --configuration "{ServiceConfiguration}" \
--extensions "[{\\"name\\":\\"RDPExtension\\",\\"properties\\":{\\"type\\":\\"RDP\\",\\"autoUpgradeMinorVersion\\":fals\
e,\\"protectedSettings\\":\\"<PrivateConfig><Password>{password}</Password></PrivateConfig>\\",\\"publisher\\":\\"Micro\
soft.Windows.Azure.Extensions\\",\\"settings\\":\\"<PublicConfig><UserName>UserAzure</UserName><Expiration>10/22/2021 \
15:05:45</Expiration></PublicConfig>\\",\\"typeHandlerVersion\\":\\"1.2.1\\"}}]" --load-balancer-configurations \
"[{\\"name\\":\\"contosolb\\",\\"properties\\":{\\"frontendIPConfigurations\\":[{\\"name\\":\\"contosofe\\",\\"properti\
es\\":{\\"publicIPAddress\\":{\\"id\\":\\"/subscriptions/{subscription-id}/resourceGroups/ConstosoRG/providers/Microsof\
t.Network/publicIPAddresses/contosopublicip\\"}}}]}}]" --package-url "{PackageUrl}" --roles \
"[{\\"name\\":\\"ContosoFrontend\\",\\"sku\\":{\\"name\\":\\"Standard_D1_v2\\",\\"capacity\\":1,\\"tier\\":\\"Standard\
\\"}}]" --upgrade-mode "Auto" --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesCreateOrUpdate#Create">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|
|**--location**|string|Resource location.|location|location|
|**--tags**|dictionary|Resource tags.|tags|tags|
|**--package-url**|string|Specifies a URL that refers to the location of the service package in the Blob service. The service package URL can be Shared Access Signature (SAS) URI from any storage account. This is a write-only property and is not returned in GET calls.|package_url|packageUrl|
|**--configuration**|string|Specifies the XML service configuration (.cscfg) for the cloud service.|configuration|configuration|
|**--configuration-url**|string|Specifies a URL that refers to the location of the service configuration in the Blob service. The service package URL  can be Shared Access Signature (SAS) URI from any storage account. This is a write-only property and is not returned in GET calls.|configuration_url|configurationUrl|
|**--start-cloud-service**|boolean|(Optional) Indicates whether to start the cloud service immediately after it is created. The default value is `true`. If false, the service model is still deployed, but the code is not run immediately. Instead, the service is PoweredOff until you call Start, at which time the service will be started. A deployed service still incurs charges, even if it is poweredoff.|start_cloud_service|startCloudService|
|**--allow-model-override**|boolean|(Optional) Indicates whether the role sku properties (roleProfile.roles.sku) specified in the model/template should override the role instance count and vm size specified in the .cscfg and .csdef respectively. The default value is `false`.|allow_model_override|allowModelOverride|
|**--upgrade-mode**|choice|Update mode for the cloud service. Role instances are allocated to update domains when the service is deployed. Updates can be initiated manually in each update domain or initiated automatically in all update domains. Possible Values are <br /><br />**Auto**<br /><br />**Manual** <br /><br />**Simultaneous**<br /><br /> If not specified, the default value is Auto. If set to Manual, PUT UpdateDomain must be called to apply the update. If set to Auto, the update is automatically applied to each update domain in sequence.|upgrade_mode|upgradeMode|
|**--extensions**|array|List of extensions for the cloud service.|extensions|extensions|
|**--load-balancer-configurations**|array|List of Load balancer configurations. Cloud service can have up to two load balancer configurations, corresponding to a Public Load Balancer and an Internal Load Balancer.|load_balancer_configurations|loadBalancerConfigurations|
|**--id**|string|Resource Id|id|id|
|**--secrets**|array|Specifies set of certificates that should be installed onto the role instances.|secrets|secrets|
|**--roles**|array|List of roles for the cloud service.|roles|roles|

#### <a name="CloudServicesDelete">Command `az vm cloud-service delete`</a>

##### <a name="ExamplesCloudServicesDelete">Example</a>
```
az vm cloud-service delete --name "{cs-name}" --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesDelete">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|

#### <a name="CloudServicesDeleteInstances">Command `az vm cloud-service delete-instance`</a>

##### <a name="ExamplesCloudServicesDeleteInstances">Example</a>
```
az vm cloud-service delete-instance --name "{cs-name}" --role-instances "ContosoFrontend_IN_0" "ContosoBackend_IN_1" \
--resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesDeleteInstances">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|
|**--role-instances**|array|List of cloud service role instance names. Value of '*' will signify all role instances of the cloud service.|role_instances|roleInstances|

#### <a name="CloudServicesListAll">Command `az vm cloud-service list-all`</a>

##### <a name="ExamplesCloudServicesListAll">Example</a>
```
az vm cloud-service list-all
```
##### <a name="ParametersCloudServicesListAll">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
#### <a name="CloudServicesPowerOff">Command `az vm cloud-service power-off`</a>

##### <a name="ExamplesCloudServicesPowerOff">Example</a>
```
az vm cloud-service power-off --name "{cs-name}" --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesPowerOff">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|

#### <a name="CloudServicesRestart">Command `az vm cloud-service restart`</a>

##### <a name="ExamplesCloudServicesRestart">Example</a>
```
az vm cloud-service restart --name "{cs-name}" --role-instances "ContosoFrontend_IN_0" "ContosoBackend_IN_1" \
--resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesRestart">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|
|**--role-instances**|array|List of cloud service role instance names. Value of '*' will signify all role instances of the cloud service.|role_instances|roleInstances|

#### <a name="CloudServicesGetInstanceView">Command `az vm cloud-service show-instance-view`</a>

##### <a name="ExamplesCloudServicesGetInstanceView">Example</a>
```
az vm cloud-service show-instance-view --name "{cs-name}" --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesGetInstanceView">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|

#### <a name="CloudServicesStart">Command `az vm cloud-service start`</a>

##### <a name="ExamplesCloudServicesStart">Example</a>
```
az vm cloud-service start --name "{cs-name}" --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesStart">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|

### group `az vm cloud-service-role`
#### <a name="CloudServiceRolesList">Command `az vm cloud-service-role list`</a>

##### <a name="ExamplesCloudServiceRolesList">Example</a>
```
az vm cloud-service-role list --cloud-service-name "{cs-name}" --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServiceRolesList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string||resource_group_name|resourceGroupName|
|**--cloud-service-name**|string||cloud_service_name|cloudServiceName|

#### <a name="CloudServiceRolesGet">Command `az vm cloud-service-role show`</a>

##### <a name="ExamplesCloudServiceRolesGet">Example</a>
```
az vm cloud-service-role show --cloud-service-name "{cs-name}" --resource-group "ConstosoRG" --role-name "{role-name}"
```
##### <a name="ParametersCloudServiceRolesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--role-name**|string|Name of the role.|role_name|roleName|
|**--resource-group-name**|string||resource_group_name|resourceGroupName|
|**--cloud-service-name**|string||cloud_service_name|cloudServiceName|

### group `az vm cloud-service-role-instance`
#### <a name="CloudServiceRoleInstancesList">Command `az vm cloud-service-role-instance list`</a>

##### <a name="ExamplesCloudServiceRoleInstancesList">Example</a>
```
az vm cloud-service-role-instance list --cloud-service-name "{cs-name}" --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServiceRoleInstancesList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string||resource_group_name|resourceGroupName|
|**--cloud-service-name**|string||cloud_service_name|cloudServiceName|

#### <a name="CloudServiceRoleInstancesGet">Command `az vm cloud-service-role-instance show`</a>

##### <a name="ExamplesCloudServiceRoleInstancesGet">Example</a>
```
az vm cloud-service-role-instance show --cloud-service-name "{cs-name}" --resource-group "ConstosoRG" \
--role-instance-name "{roleInstance-name}"
```
##### <a name="ParametersCloudServiceRoleInstancesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--role-instance-name**|string|Name of the role instance.|role_instance_name|roleInstanceName|
|**--resource-group-name**|string||resource_group_name|resourceGroupName|
|**--cloud-service-name**|string||cloud_service_name|cloudServiceName|

#### <a name="CloudServiceRoleInstancesReimage">Command `az vm cloud-service-role-instance reimage`</a>

##### <a name="ExamplesCloudServiceRoleInstancesReimage">Example</a>
```
az vm cloud-service-role-instance reimage --cloud-service-name "{cs-name}" --resource-group "ConstosoRG" \
--role-instance-name "{roleInstance-name}"
```
##### <a name="ParametersCloudServiceRoleInstancesReimage">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--role-instance-name**|string|Name of the role instance.|role_instance_name|roleInstanceName|
|**--resource-group-name**|string||resource_group_name|resourceGroupName|
|**--cloud-service-name**|string||cloud_service_name|cloudServiceName|

#### <a name="CloudServiceRoleInstancesRestart">Command `az vm cloud-service-role-instance restart`</a>

##### <a name="ExamplesCloudServiceRoleInstancesRestart">Example</a>
```
az vm cloud-service-role-instance restart --cloud-service-name "{cs-name}" --resource-group "ConstosoRG" \
--role-instance-name "{roleInstance-name}"
```
##### <a name="ParametersCloudServiceRoleInstancesRestart">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--role-instance-name**|string|Name of the role instance.|role_instance_name|roleInstanceName|
|**--resource-group-name**|string||resource_group_name|resourceGroupName|
|**--cloud-service-name**|string||cloud_service_name|cloudServiceName|

#### <a name="CloudServiceRoleInstancesGetInstanceView">Command `az vm cloud-service-role-instance show-instance-view`</a>

##### <a name="ExamplesCloudServiceRoleInstancesGetInstanceView">Example</a>
```
az vm cloud-service-role-instance show-instance-view --cloud-service-name "{cs-name}" --resource-group "ConstosoRG" \
--role-instance-name "{roleInstance-name}"
```
##### <a name="ParametersCloudServiceRoleInstancesGetInstanceView">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--role-instance-name**|string|Name of the role instance.|role_instance_name|roleInstanceName|
|**--resource-group-name**|string||resource_group_name|resourceGroupName|
|**--cloud-service-name**|string||cloud_service_name|cloudServiceName|

#### <a name="CloudServiceRoleInstancesGetRemoteDesktopFile">Command `az vm cloud-service-role-instance show-remote-desktop-file`</a>

##### <a name="ParametersCloudServiceRoleInstancesGetRemoteDesktopFile">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--role-instance-name**|string|Name of the role instance.|role_instance_name|roleInstanceName|
|**--resource-group-name**|string||resource_group_name|resourceGroupName|
|**--cloud-service-name**|string||cloud_service_name|cloudServiceName|

### group `az vm cloud-service-update-domain`
#### <a name="CloudServicesUpdateDomainListUpdateDomains">Command `az vm cloud-service-update-domain list-update-domain`</a>

##### <a name="ExamplesCloudServicesUpdateDomainListUpdateDomains">Example</a>
```
az vm cloud-service-update-domain list-update-domain --cloud-service-name "{cs-name}" --resource-group "ConstosoRG"
```
##### <a name="ParametersCloudServicesUpdateDomainListUpdateDomains">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|

#### <a name="CloudServicesUpdateDomainGetUpdateDomain">Command `az vm cloud-service-update-domain show-update-domain`</a>

##### <a name="ExamplesCloudServicesUpdateDomainGetUpdateDomain">Example</a>
```
az vm cloud-service-update-domain show-update-domain --cloud-service-name "{cs-name}" --resource-group "ConstosoRG" \
--update-domain 1
```
##### <a name="ParametersCloudServicesUpdateDomainGetUpdateDomain">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|
|**--update-domain**|integer|Specifies an integer value that identifies the update domain. Update domains are identified with a zero-based index: the first update domain has an ID of 0, the second has an ID of 1, and so on.|update_domain|updateDomain|

#### <a name="CloudServicesUpdateDomainWalkUpdateDomain">Command `az vm cloud-service-update-domain walk-update-domain`</a>

##### <a name="ExamplesCloudServicesUpdateDomainWalkUpdateDomain">Example</a>
```
az vm cloud-service-update-domain walk-update-domain --cloud-service-name "{cs-name}" --resource-group "ConstosoRG" \
--update-domain 1
```
##### <a name="ParametersCloudServicesUpdateDomainWalkUpdateDomain">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|Name of the resource group.|resource_group_name|resourceGroupName|
|**--cloud-service-name**|string|Name of the cloud service.|cloud_service_name|cloudServiceName|
|**--update-domain**|integer|Specifies an integer value that identifies the update domain. Update domains are identified with a zero-based index: the first update domain has an ID of 0, the second has an ID of 1, and so on.|update_domain|updateDomain|

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

#### <a name="DiskAccessesListPrivateEndpointConnections">Command `az vm disk-access list-private-endpoint-connection`</a>

##### <a name="ExamplesDiskAccessesListPrivateEndpointConnections">Example</a>
```
az vm disk-access list-private-endpoint-connection --name "myDiskAccess" --resource-group "myResourceGroup"
```
##### <a name="ParametersDiskAccessesListPrivateEndpointConnections">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--disk-access-name**|string|The name of the disk access resource that is being created. The name can't be changed after the disk encryption set is created. Supported characters for the name are a-z, A-Z, 0-9 and _. The maximum name length is 80 characters.|disk_access_name|diskAccessName|

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

### group `az vm disk-restore-point`
#### <a name="DiskRestorePointGet">Command `az vm disk-restore-point show`</a>

##### <a name="ExamplesDiskRestorePointGet">Example</a>
```
az vm disk-restore-point show --name "TestDisk45ceb03433006d1baee0_b70cd924-3362-4a80-93c2-9415eaa12745" \
--resource-group "myResourceGroup" --restore-point-collection-name "rpc" --vm-restore-point-name "vmrp"
```
##### <a name="ParametersDiskRestorePointGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--restore-point-collection-name**|string|The name of the restore point collection that the disk restore point belongs. Supported characters for the name are a-z, A-Z, 0-9 and _. The maximum name length is 80 characters.|restore_point_collection_name|restorePointCollectionName|
|**--vm-restore-point-name**|string|The name of the vm restore point that the disk disk restore point belongs. Supported characters for the name are a-z, A-Z, 0-9 and _. The maximum name length is 80 characters.|vm_restore_point_name|vmRestorePointName|
|**--disk-restore-point-name**|string|The name of the disk restore point created. Supported characters for the name are a-z, A-Z, 0-9 and _. The maximum name length is 80 characters.|disk_restore_point_name|diskRestorePointName|

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

### group `az vm virtual-machine`
#### <a name="VirtualMachinesInstallPatches">Command `az vm virtual-machine install-patch`</a>

##### <a name="ExamplesVirtualMachinesInstallPatches">Example</a>
```
az vm virtual-machine install-patch --maximum-duration "PT4H" --reboot-setting "IfRequired" --windows-parameters \
classifications-to-include="Critical" classifications-to-include="Security" max-patch-publish-date="2020-11-19T02:36:43\
.0539904+00:00" --resource-group "myResourceGroupName" --name "myVMName"
```
##### <a name="ParametersVirtualMachinesInstallPatches">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--resource-group-name**|string|The name of the resource group.|resource_group_name|resourceGroupName|
|**--vm-name**|string|The name of the virtual machine.|vm_name|vmName|
|**--maximum-duration**|string|Specifies the maximum amount of time that the operation will run. It must be an ISO 8601-compliant duration string such as PT4H (4 hours)|maximum_duration|maximumDuration|
|**--reboot-setting**|choice|Defines when it is acceptable to reboot a VM during a software update operation.|reboot_setting|rebootSetting|
|**--windows-parameters**|object|Input for InstallPatches on a Windows VM, as directly received by the API|windows_parameters|windowsParameters|
|**--linux-parameters**|object|Input for InstallPatches on a Linux VM, as directly received by the API|linux_parameters|linuxParameters|

#### <a name="VirtualMachinesReimage">Command `az vm virtual-machine reimage`</a>

##### <a name="ExamplesVirtualMachinesReimage">Example</a>
```
az vm virtual-machine reimage --temp-disk true --resource-group "myResourceGroup" --name "myVMName"
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
