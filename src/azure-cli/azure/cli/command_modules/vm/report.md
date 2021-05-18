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
|az sig shared-gallery|SharedGalleries|[commands](#CommandsInSharedGalleries)|
|az sig shared-image-definition|SharedGalleryImages|[commands](#CommandsInSharedGalleryImages)|
|az sig shared-image-version|SharedGalleryImageVersions|[commands](#CommandsInSharedGalleryImageVersions)|

## COMMANDS
### <a name="CommandsInSharedGalleries">Commands in `az sig shared-gallery` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az sig shared-gallery list](#SharedGalleriesList)|List|[Parameters](#ParametersSharedGalleriesList)|[Example](#ExamplesSharedGalleriesList)|
|[az sig shared-gallery show](#SharedGalleriesGet)|Get|[Parameters](#ParametersSharedGalleriesGet)|[Example](#ExamplesSharedGalleriesGet)|

### <a name="CommandsInSharedGalleryImages">Commands in `az sig shared-image-definition` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az sig shared-image-definition list](#SharedGalleryImagesList)|List|[Parameters](#ParametersSharedGalleryImagesList)|[Example](#ExamplesSharedGalleryImagesList)|
|[az sig shared-image-definition show](#SharedGalleryImagesGet)|Get|[Parameters](#ParametersSharedGalleryImagesGet)|[Example](#ExamplesSharedGalleryImagesGet)|

### <a name="CommandsInSharedGalleryImageVersions">Commands in `az sig shared-image-version` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az sig shared-image-version list](#SharedGalleryImageVersionsList)|List|[Parameters](#ParametersSharedGalleryImageVersionsList)|[Example](#ExamplesSharedGalleryImageVersionsList)|
|[az sig shared-image-version show](#SharedGalleryImageVersionsGet)|Get|[Parameters](#ParametersSharedGalleryImageVersionsGet)|[Example](#ExamplesSharedGalleryImageVersionsGet)|

### <a name="CommandsInSshPublicKeys">Commands in `az sshkey` group</a>
|CLI Command|Operation Swagger name|Parameters|Examples|
|---------|------------|--------|-----------|
|[az sshkey list](#SshPublicKeysListByResourceGroup)|ListByResourceGroup|[Parameters](#ParametersSshPublicKeysListByResourceGroup)|Not Found|
|[az sshkey list](#SshPublicKeysListBySubscription)|ListBySubscription|[Parameters](#ParametersSshPublicKeysListBySubscription)|Not Found|
|[az sshkey show](#SshPublicKeysGet)|Get|[Parameters](#ParametersSshPublicKeysGet)|[Example](#ExamplesSshPublicKeysGet)|
|[az sshkey create](#SshPublicKeysCreate)|Create|[Parameters](#ParametersSshPublicKeysCreate)|[Example](#ExamplesSshPublicKeysCreate)|
|[az sshkey update](#SshPublicKeysUpdate)|Update|[Parameters](#ParametersSshPublicKeysUpdate)|Not Found|
|[az sshkey delete](#SshPublicKeysDelete)|Delete|[Parameters](#ParametersSshPublicKeysDelete)|Not Found|


## COMMAND DETAILS

### group `az sig shared-gallery`
#### <a name="SharedGalleriesList">Command `az sig shared-gallery list`</a>

##### <a name="ExamplesSharedGalleriesList">Example</a>
```
az sig shared-gallery list --location "myLocation"
```
##### <a name="ParametersSharedGalleriesList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--location**|string|Resource location.|location|location|
|**--shared-to**|choice|The query parameter to decide what shared galleries to fetch when doing listing operations.|shared_to|sharedTo|

#### <a name="SharedGalleriesGet">Command `az sig shared-gallery show`</a>

##### <a name="ExamplesSharedGalleriesGet">Example</a>
```
az sig shared-gallery show --gallery-unique-name "galleryUniqueName" --location "myLocation"
```
##### <a name="ParametersSharedGalleriesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--location**|string|Resource location.|location|location|
|**--gallery-unique-name**|string|The unique name of the Shared Gallery.|gallery_unique_name|galleryUniqueName|

### group `az sig shared-image-definition`
#### <a name="SharedGalleryImagesList">Command `az sig shared-image-definition list`</a>

##### <a name="ExamplesSharedGalleryImagesList">Example</a>
```
az sig shared-image-definition list --gallery-unique-name "galleryUniqueName" --location "myLocation"
```
##### <a name="ParametersSharedGalleryImagesList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--location**|string|Resource location.|location|location|
|**--gallery-unique-name**|string|The unique name of the Shared Gallery.|gallery_unique_name|galleryUniqueName|
|**--shared-to**|choice|The query parameter to decide what shared galleries to fetch when doing listing operations.|shared_to|sharedTo|

#### <a name="SharedGalleryImagesGet">Command `az sig shared-image-definition show`</a>

##### <a name="ExamplesSharedGalleryImagesGet">Example</a>
```
az sig shared-image-definition show --gallery-image-definition "myGalleryImageName" --gallery-unique-name \
"galleryUniqueName" --location "myLocation"
```
##### <a name="ParametersSharedGalleryImagesGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--location**|string|Resource location.|location|location|
|**--gallery-unique-name**|string|The unique name of the Shared Gallery.|gallery_unique_name|galleryUniqueName|
|**--gallery-image-name**|string|The name of the Shared Gallery Image Definition from which the Image Versions are to be listed.|gallery_image_name|galleryImageName|

### group `az sig shared-image-version`
#### <a name="SharedGalleryImageVersionsList">Command `az sig shared-image-version list`</a>

##### <a name="ExamplesSharedGalleryImageVersionsList">Example</a>
```
az sig shared-image-version list --gallery-image-definition "myGalleryImageName" --gallery-unique-name \
"galleryUniqueName" --location "myLocation"
```
##### <a name="ParametersSharedGalleryImageVersionsList">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--location**|string|Resource location.|location|location|
|**--gallery-unique-name**|string|The unique name of the Shared Gallery.|gallery_unique_name|galleryUniqueName|
|**--gallery-image-name**|string|The name of the Shared Gallery Image Definition from which the Image Versions are to be listed.|gallery_image_name|galleryImageName|
|**--shared-to**|choice|The query parameter to decide what shared galleries to fetch when doing listing operations.|shared_to|sharedTo|

#### <a name="SharedGalleryImageVersionsGet">Command `az sig shared-image-version show`</a>

##### <a name="ExamplesSharedGalleryImageVersionsGet">Example</a>
```
az sig shared-image-version show --gallery-image-definition "myGalleryImageName" --gallery-image-version \
"myGalleryImageVersionName" --gallery-unique-name "galleryUniqueName" --location "myLocation"
```
##### <a name="ParametersSharedGalleryImageVersionsGet">Parameters</a> 
|Option|Type|Description|Path (SDK)|Swagger name|
|------|----|-----------|----------|------------|
|**--location**|string|Resource location.|location|location|
|**--gallery-unique-name**|string|The unique name of the Shared Gallery.|gallery_unique_name|galleryUniqueName|
|**--gallery-image-name**|string|The name of the Shared Gallery Image Definition from which the Image Versions are to be listed.|gallery_image_name|galleryImageName|
|**--gallery-image-version-name**|string|The name of the gallery image version to be created. Needs to follow semantic version name pattern: The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. Format: <MajorVersion>.<MinorVersion>.<Patch>|gallery_image_version_name|galleryImageVersionName|

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
