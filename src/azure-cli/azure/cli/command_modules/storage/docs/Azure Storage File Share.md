## Azure File Share

Azure Files offers fully managed file shares in the cloud that are accessible via the industry standard Server Message 
Block (SMB) protocol. 

Azure supports multiple types of storage accounts for different storage scenarios customers may have, but there are 
two main types of storage accounts for Azure Files. Which storage account type you need to create depends on whether 
you want to create a standard file share or a premium file share:

- General purpose version 2 (GPv2) storage accounts: 

GPv2 storage accounts allow you to deploy Azure file shares on standard/hard disk-based (HDD-based) hardware. In addition to storing Azure file shares, GPv2 storage accounts can store other storage resources such as blob containers, queues, or tables.

```
az storage account create \
    --kind StorageV2 \
    --name mystorageaccount \
    -g myresourcegroup
```

- FileStorage storage accounts: 

FileStorage storage accounts allow you to deploy Azure file shares on premium/solid-state disk-based (SSD-based) hardware. FileStorage accounts can only be used to store Azure file shares; no other storage resources (blob containers, queues, tables, etc.) can be deployed in a FileStorage account.

```
az storage account create \
    --kind FileShare \
    --sku Premium_LRS \
    --name mystorageaccount \
    -g myresourcegroup
```

Note:

If you want to support large file share with more than 5 TiB capacity, please add `--enable-large-file-share` in `az storage account create`.

### Overview
There are two main file share usage scenario in Azure CLI as shown below:

```
❯ az storage share-rm -h

Group
    az storage share-rm : Manage Azure file shares using the Microsoft.Storage resource provider.
        This command group is in preview. It may be changed/removed in a future release.
Commands:
    create : Create a new Azure file share under the specified storage account.
    delete : Delete the specified Azure file share.
    exists : Check for the existence of an Azure file share.
    list   : List the Azure file shares under the specified storage account.
    show   : Show the properties for a specified Azure file share.
    update : Update the properties for an Azure file share.

For more specific examples, use: az find "az storage share-rm"
```
Note:
If you want to bypass firewall and https is support for your storage account, you could use command in `az storage share-rm` to manage your file share.


```
❯ az storage share -h

Group
    az storage share : Manage file shares.

Subgroups:
    metadata     : Manage the metadata of a file share.
    policy       : Manage shared access policies of a storage file share.

Commands:
    create       : Creates a new share under the specified account.
    delete       : Marks the specified share for deletion.
    exists       : Check for the existence of a file share.
    generate-sas : Generates a shared access signature for the share.
    list         : List the file shares in a storage account.
    show         : Returns all user-defined metadata and system properties for the specified share.
    snapshot     : Creates a snapshot of an existing share under the specified account.
    stats        : Gets the approximate size of the data stored on the share, rounded up to the
                   nearest gigabyte.
    update       : Sets service-defined properties for the specified share.
    url          : Create a URI to access a file share.

For more specific examples, use: az find "az storage share"
```
Note:
If you have storage account related credential, you could use command in `az storage share` to manage your file share.

#### Manage File Share with `az storage share-rm`
##### Create a file share
- Create a file share with storage account name and resource group name
```
az storage share-rm create \
    -n sharename \
    --quota 10
    --storage-account mystorageaccount
    -g myresourcegroup
```

- Create a file share with storage account resource id and enable NFS protocol
```
az storage share-rm create \
    -n sharename \
    --quota 10
    --enabled-protocols NFS \
    --root-squash AllSquash \
    --storage-account "/subscriptions/musub/resourceGroups/myresourcegroup/providers/Microsoft.Storage/storageAccounts/mystorageaccunt"
```

##### Show the properties for a specified Azure file share
```
az storage share-rm show \
    -n sharename \
    --storage-account mystorageaccount \
    -g myresourcegroup
```

##### Update the properties for an Azure file share
- Update quota for file share

```
az storage share-rm update \
    --quota 10 \
    -n sharename \
    --storage-account mystroageaccount 
    -g myresourcegroup 
```

#####  List the Azure file shares under the specified storage account
```
az storage share-rm list \
    --storage-account mystorageaccount
    -g myresourcegroup
```

##### Delete the specified Azure file share
- Delete file share with prompt

```
az storage share-rm delete \
    -n sharename \
    --storage-account mystorageaccount \
    -g my resourcegroup
```

- Delete file share without prompt

```
az storage share-rm delete \
    -n sharename \
    --storage-account mystorageaccount \
    -g my resourcegroup \
    -y
```
