# Azure CLI Storage Module #
This is a main module for storage features.

### Included Features

#### Management Policy:	
Manage data policy rules associated with a storage account: [more info](https://learn.microsoft.com/azure/storage/common/storage-lifecycle-managment-concepts)\	
*Examples:*	
```	
az storage account management-policy create \	
    --account-name accountName \	
    --resource-group groupName \	
    --policy @{path}	
```	

#### Static Website:	
Manage static website configurations: [more info](https://learn.microsoft.com/azure/storage/blobs/storage-blob-static-website)\	
*Examples:*	
```	
az storage blob service-properties update \	
    --account-name accountName \	
    --static-website \	
    --404-document error.html \	
    --index-document index.html	
```	

#### Hierarchical Namespace:	
Enable the blob service to exhibit filesystem semantics: [more info](https://learn.microsoft.com/azure/storage/data-lake-storage/namespace)\	
*Examples:*	
```	
az storage account create \	
    --name accountName \	
    --resource-group groupName \	
    --kind StorageV2 \	
    --enable-hierarchical-namespace	
```	

#### File AAD Integration:	
Enable AAD integration for Azure files, which will support SMB access: [more info](https://learn.microsoft.com/azure/storage/files/storage-files-active-directory-enable)\	
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
More info:[premium blobs](https://azure.microsoft.com/blog/introducing-azure-premium-blob-storage-limited-public-preview/) [premium files](https://learn.microsoft.com/azure/storage/files/storage-files-introduction)\	
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
Failover GRS/RA-GRS storage accounts from the primary cluster to the secondary cluster: [more info](https://learn.microsoft.com/azure/storage/common/storage-disaster-recovery-guidance)\	
*Examples:*	
```	
az storage account show \	
    --name accountName \	
    --expand geoReplicationStats	
az storage account failover \	
    --name accountName	
```

#### Storage Management Resource Groups

The following built-in command groups use Storage Management API `2026-09-01`:

| Command group | Operations |
| --- | --- |
| `az storage account connector` | Create, update, delete, show, list, test an existing connection, wait |
| `az storage account data-share` | Create, update, delete, show, list, wait |
| `az storage account blob-access-point-configuration` | Create, update, delete, show, list, test existing/proposed connections, wait |
| `az storage context-cache` | Create, update, delete, show, list, check name availability, wait |
| `az storage context-cache container` | Create, update, delete, show, list, wait |
| `az storage context-cache identity` | Assign, remove, show managed identities |

Use each command's `--help` for its required arguments and examples. Long-running
connection tests support `--no-wait`; they do not have a separate test-result wait
command. Storage task assignments, including `az storage account task-assignment stop`,
remain in the `storage-preview` extension.

##### Data-share collection updates

Creating a data share requires both `--assets` and `--access-policies`; explicit
empty arrays are allowed:

```azurecli
az storage account data-share create \
    --resource-group MyResourceGroup --account-name mystorageaccount \
    --name myshare --location eastus --assets '[]' --access-policies '[]'
```

Updates use PATCH. An omitted or `null` collection preserves the existing value;
an empty array clears it; a non-empty array replaces the entire collection.
For example, `--assets '[]'` clears the share's assets without modifying omitted
access policies. Connector, data-share and Blob Access Point configuration
updates do not resend create-only properties or inject argument defaults.

##### Polymorphic connection inputs

The `--source` argument uses nested CLI discriminator names rather than the
service's raw discriminator fields. For example, a Blob Access Point configuration
can use the following source object:

```json
{
  "s3-compatible": {
    "connection": {
      "endpoint": {
        "endpoint": "https://s3.example.com"
      }
    },
    "auth": {
      "access-key": {
        "access-key-id": "<access-key-id>",
        "secret-access-key": "<secret-access-key>"
      }
    }
  }
}
```

Other source variants are `net-app-ontap`, `azure-net-app-files`, `dell-one-fs`,
`qumulo`, `commvault` and `nasuni`. Connections support `endpoint` and `private-link`.
Use the nested argument help to see required Private Link fields. Remote access
keys are write-only: show/list responses do not include `secretAccessKey`.
Keep input files containing credentials out of version control and shell history.

Connectors instead use a `data-share` source with `connection.data-share.data-share-uri`
and `auth-properties.managed-identity.identity-resource-id`. The URI and identity
must identify an accessible data share and managed identity respectively.

##### Context cache updates and identities

Context caches support both system-assigned and user-assigned managed identities.
Use `az storage context-cache identity assign/remove/show` to manage identities.
These helpers preserve unrelated cache properties and identities not selected
for removal.

Cache and cache-container updates use PATCH. Cache `account-kind` and container
`model-name`/`provider` are create-only. Container `--time-to-live` accepts 1 through
30 inclusive. `az storage context-cache list` works across the subscription or
within a specified resource group. `az storage context-cache check-name --name NAME`
checks availability with the resource type defaulted to `Microsoft.Storage/contextCaches`.
