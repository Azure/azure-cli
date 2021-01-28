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

## COMMANDS
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


## COMMAND DETAILS

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
