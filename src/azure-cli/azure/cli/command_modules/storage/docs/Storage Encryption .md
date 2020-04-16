## Azure Storage Encryption
Azure Storage automatically encrypts your data when it is persisted it to the cloud. Azure Storage encryption protects your data and to help you to meet your organizational security and compliance commitments. 
See more in
https://docs.microsoft.com/en-us/azure/storage/common/storage-service-encryption?toc=/azure/storage/blobs/toc.json

### Included Features

#### Manage encryption for storage account

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

#### Enable key auto-rotation for existing cmk
```
az storage account update \
    --account-name mystorageaccount \
    --encryption-key-version ""
```

#### Enable key auto-rotation for existing cmk
```
az storage account update \
    --account-name mystorageaccount \
    --encryption-key-version ""
```

#### Change key source to Microsoft.Storage
```
az storage account update \
    --account-name mystorageaccount \
    --encryption-key-source Microsoft.Storage
```
