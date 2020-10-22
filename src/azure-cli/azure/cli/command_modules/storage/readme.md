# Azure CLI Storage Module #
This is a main module for storage features.

### Included Features

#### Management Policy:	
Manage data policy rules associated with a storage account: [more info](https://docs.microsoft.com/azure/storage/common/storage-lifecycle-managment-concepts)\	
*Examples:*	
```	
az storage account management-policy create \	
    --account-name accountName \	
    --resource-group groupName \	
    --policy @{path}	
```	

#### Static Website:	
Manage static website configurations: [more info](https://docs.microsoft.com/azure/storage/blobs/storage-blob-static-website)\	
*Examples:*	
```	
az storage blob service-properties update \	
    --account-name accountName \	
    --static-website \	
    --404-document error.html \	
    --index-document index.html	
```	

#### Hierarchical Namespace:	
Enable the blob service to exhibit filesystem semantics: [more info](https://docs.microsoft.com/azure/storage/data-lake-storage/namespace)\	
*Examples:*	
```	
az storage account create \	
    --name accountName \	
    --resource-group groupName \	
    --kind StorageV2 \	
    --enable-hierarchical-namespace	
```	

#### File AAD Integration:	
Enable AAD integration for Azure files, which will support SMB access: [more info](https://docs.microsoft.com/azure/storage/files/storage-files-active-directory-enable)\	
*Examples:*	
```	
az storage account create \	
    --name accountName \	
    --resource-group groupName \	
    --kind StorageV2	
az storage account update \	
    --name accountName \	
    --resource-group groupName	
```	

#### Premium Blobs/Files:	
Create premium blob/file storage accounts.\	
More info:[premium blobs](https://azure.microsoft.com/blog/introducing-azure-premium-blob-storage-limited-public-preview/) [premium files](https://docs.microsoft.com/azure/storage/files/storage-files-introduction)\	
*Examples:*	
```	
az storage account create \	
    --name accountName \	
    --resource-group groupName \	
    --sku Premium_LRS \	
    --kind BlockBlobStorage	
az storage account create \	
    --name accountName \	
    --resource-group groupName \	
    --sku Premium_LRS \	
    --kind FileStorage	
```	

#### Customer-Controlled Failover:	
Failover GRS/RA-GRS storage accounts from the primary cluster to the secondary cluster: [more info](https://docs.microsoft.com/azure/storage/common/storage-disaster-recovery-guidance)\	
*Examples:*	
```	
az storage account show \	
    --name accountName \	
    --expand geoReplicationStats	
az storage account failover \	
    --name accountName	
```
