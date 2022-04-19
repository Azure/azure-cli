# Storage Data Plane Commands Auth

Azure operations can be divided into two categories - control plane and data plane. By running storage data plane commands, requests will be sent directly to Storage service instead of being sent to ARM(Azure Resource Manager). Hence additional credentials are required for successfully auth to Storage service.

## Authorization Options

There are several ways to authorize for storage data plane commands:

### Azure Active Directory integration

By specifying `--auth-mode login`, CLI will use the OAuth token returned by AAD(Azure Active Directory) to authorize requests against Storage service.

Here's an example of getting properties of a blob in a storage account with AAD token
```cmd
# Get blob properties using AAD token
> az storage blob show --name $blobName --container-name $containerName --account-name $accountName --auth-mode login
```

### Shared key authorization

By specifying `--account-key $accountKey` or `--connection-string $connectionString` configured using account key, CLI can use Shared Key by signing each request with the storage account access key.

Here's an example of getting properties of a blob in a storage account with account key
```cmd
# Get storage account access key
> $accountKey = az storage account keys list --account-name $accountName --resource-group $rgName --query "[0].value"
# Get blob properties with account key
> az storage blob show --name $blobName --container-name $containerName --account-name $accountName --account-key $accountKey
```

Here's an example of getting properties of a blob in a storage account with connection string configured using account key
```cmd
# Get storage account access key
> $accountKey = az storage account keys list --account-name $accountName --resource-group $rgName --query "[0].value"
# Configure a connection string
> $connectionString = "DefaultEndpointsProtocol=https;AccountName=$accountName;AccountKey=$accountKey"
# Get blob properties with connection string
> az storage blob show --name $blobName --container-name $containerName --connection-string $connectionString
```

### Shared access signatures

By specifying `--sas-token $sasToken` or `--connection-string $connectionString` configured using shared access signature(SAS), CLI can get a signed URI including a token that indicates how the resources may be accessed by the client.

Here's an example of getting properties of a blob in a storage account with sas token
```
# Generate a sas(Shared access signature) token
> az storage account/container/blob/share/fs/queue/table generate-sas
# Get blob properties with sas token
> az storage blob show --name $blobName --container-name $containerName --account-name $accountName --sas-token $sasToken
```

Here's an example of getting properties of a blob in a storage account with connection string configured using sas
```
# Generate a sas(Shared access signature) token
> az storage account/container/blob/share/fs/queue/table generate-sas
# Configure a connection string(Each service endpoint is optional, although the connection string must contain at least one.)
> $connectionString = "BlobEndpoint=$blobEndpoint;QueueEndpoint=$queueEndpoint;TableEndpoint=$tableEndpoint;FileEndpoint=$fileEndpoint;SharedAccessSignature=$sasToken"
# Get blob properties with connection string
> az storage blob show --name $blobName --container-name $containerName --connection-string $connectionString
```

## CLI default option

If no `--auth-mode` or `--account-key` or `--sas-token` or `--connection-string` provided, CLI will query for account key by default. This requires sending control plane requests:
* Listing all storage accounts and finding the resource group which your storage account belongs to
* Querying the storage account key with account name and resource group info

Then CLI will proceed the data plane requests with the account key queried before.

## See More
[Azure control plane and data plane](https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/control-plane-and-data-plane)
[Authorize access to data in Azure Storage](https://docs.microsoft.com/en-us/azure/storage/common/authorize-data-access)
[Configure Azure Storage connection strings](https://docs.microsoft.com/en-us/azure/storage/common/storage-configure-connection-string)
