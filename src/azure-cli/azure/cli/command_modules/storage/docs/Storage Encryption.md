## Azure Storage Encryption
Azure Storage automatically encrypts your data when it is persisted it to the cloud. Azure Storage encryption protects your data and to help you to meet your organizational security and compliance commitments. 
See more in
https://docs.microsoft.com/en-us/azure/storage/common/storage-service-encryption?toc=/azure/storage/blobs/toc.json

### How to use ###
Install Azure CLI in one of the following ways:
1. [Public Released Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
2. [Try Features before Release](https://github.com/Azure/azure-cli/blob/dev/doc/try_new_features_before_release.md)

### Included Features
- [Manage encryption for storage account](#Manage-encryption-for-storage-account)
- [Manage encryption scope for storage account](#Manage-encryption-scope-for-storage-account)
- [Manage encryption scope for container](#Manage-encryption-scope-for-container)

#### Manage encryption for storage account

*Examples:*
##### Configure customer managed key for storage account
- Configure CMK for storage account with *key auto-rotation* enabled
```
az storage account update \
    --account-name mystorageaccount \
    --encryption-key-source Microsoft.Keyvault \
    --encryption-key-name mykey \
    --encryption-key-vault https://mykeyvault.vault.azure.net/
```

- Configure CMK for storage account with specific version
```
az storage account update \
    --account-name mystorageaccount \
    --encryption-key-source Microsoft.Keyvault \
    --encryption-key-name mykey \
    --encryption-key-vault https://mykeyvault.vault.azure.net/ \
    --encryption-key-version 2780bea583714f33b8051ea24f90a246
```

##### Enable key auto-rotation for existing cmk
```
az storage account update \
    --account-name mystorageaccount \
    --encryption-key-version ""
```

##### Disable key auto-rotation and pin to specific key version
```
az storage account update \
    --account-name mystorageaccount \
    --encryption-key-version 2780bea583714f33b8051ea24f90a246
```

##### Change key source to Microsoft.Storage
```
az storage account update \
    --account-name mystorageaccount \
    --encryption-key-source Microsoft.Storage
```


#### Manage encryption scope for storage account
Manage encryption scope associated with a storage account.
```
az storage account encryptipn-scope -h
```

*Examples:*
##### Create an encryption scope in a storage account based on Microsoft.Storage key source
```
az storage account encryption-scope create \
    -n myencryption \
    -s Micrsoft.Storage \
    --account-name mystorageaccount \
    -g MyResourceGroup
```

##### Show the properties of specified encryption scope in a storage account.
```
az storage account encryption-scope show \
    -n myencryption \
    --account-name mystorageaccount \
    -g MyResourceGroup
```

##### List all encryption scopes in a storage account.
```
az storage account encryption-scope list \
    --account-name mystorageaccount \
    -g MyResourceGroup
```

##### Update key source of specified encryption scope in a storage account.
```
az storage account encryption-scope update \
    -n myencryption \
    -s Micrsoft.KeyVault \
    -u "https://vaultname.vault.azure.net/keys/keyname/1f7fa7edc99f4cdf82b5b5f32f2a50a7" \
    --account-name mystorageaccount \
    -g MyResourceGoup
```

##### Disable specified encryption scope in a storage account.
```
az storage account encryption-scope update \
    -n myencryption \
    --account-name mystorageaccount \
    -g MyResourceGoup \
    --state Disabled
```

##### Enable specified encryption scope in a storage account.
```
az storage account encryption-scope update \
    -n myencryption \
    --account-name mystorageaccount \
    -g MyResourceGoup \
    --state Enabled
```

#### Manage encryption scope for container

*Examples:*
##### Set default encryption scope when creating storage container
```
az storage container create \
    -n testcontainer \
    --account-name mystorageaccount \
    -g MyResourceGroup \
    --default-encryption-scope myencryption \
    --prevent-encryption-scope-override false
```

#### Manage encryption scope for blob

*Examples:*
##### Set default encryption scope when uploading storage blob
```
az storage blob upload
    -n blobname \
    -f <filepath> \
    -c testcontainer \
    --encryption-scope myencryption \
    --account-name mystorageaccount \
    --account-key 0000-0000
```
