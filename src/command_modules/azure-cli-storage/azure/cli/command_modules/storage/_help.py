# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

# pylint: disable=line-too-long, too-many-lines

helps['storage entity insert'] = """
    type: command
    short-summary: Insert an entity into a table.
    parameters:
        - name: --table-name -t
          type: string
          short-summary: The name of the table to insert the entity into.
        - name: --entity -e
          type: list
          short-summary: Space-separated list of key=value pairs. Must contain a PartitionKey and a RowKey.
          long-summary: The PartitionKey and RowKey must be unique within the table, and may be up to 64Kb in size. If using an integer value as a key,
                        convert it to a fixed-width string which can be canonically sorted.
                        For example, convert the integer value 1 to the string value "0000001" to ensure proper sorting.
        - name: --if-exists
          type: string
          short-summary: Behavior when an entity already exists for the specified PartitionKey and RowKey.
        - name: --timeout
          short-summary: The server timeout, expressed in seconds.
"""

helps['storage blob upload'] = """
    type: command
    short-summary: Upload a file to a storage blob.
    long-summary: Creates a new blob from a file path, or updates the content of an existing blob with automatic chunking and progress notifications.
    parameters:
        - name: --type -t
          short-summary: Defaults to 'page' for *.vhd files, or 'block' otherwise.
        - name: --maxsize-condition
          short-summary: The max length in bytes permitted for an append blob.
        - name: --validate-content
          short-summary: Specifies that an MD5 hash shall be calculated for each chunk of the blob and verified by the
                         service when the chunk has arrived.
        - name: --tier
          short-summary: A page blob tier value to set the blob to. The tier correlates to the size of the blob and
                         number of allowed IOPS. This is only applicable to page blobs on premium storage accounts.
    examples:
        - name: Upload to a blob.
          text: az storage blob upload -f /path/to/file -c MyContainer -n MyBlob
"""

helps['storage file upload'] = """
    type: command
    short-summary: Upload a file to a share that uses the SMB 3.0 protocol.
    long-summary: Creates or updates an Azure file from a source path with automatic chunking and progress notifications.
    examples:
        - name: Upload to a local file to a share.
          text: az storage file upload -s MyShare -source /path/to/file
"""

helps['storage blob show'] = """
    type: command
    short-summary: Get the details of a blob.
    examples:
        - name: Show all properties of a blob.
          text: az storage blob show -c MyContainer -n MyBlob
"""

helps['storage blob delete'] = """
    type: command
    short-summary: Mark a blob or snapshot for deletion.
    long-summary: >
        The blob is marked for later deletion during garbage collection.  In order to delete a blob, all of its snapshots must also be deleted.
        Both can be removed at the same time.
    examples:
        - name: Delete a blob.
          text: az storage blob delete -c MyContainer -n MyBlob
"""

helps['storage account create'] = """
    type: command
    short-summary: Create a storage account.
    long-summary: >
        The SKU of the storage account defaults to 'Standard_RAGRS'.
    examples:
        - name: Create a storage account 'MyStorageAccount' in resource group 'MyResourceGroup' in the West US region with locally redundant storage.
          text: az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --sku Standard_LRS
          min_profile: latest
        - name: Create a storage account 'MyStorageAccount' in resource group 'MyResourceGroup' in the West US region with locally redundant storage.
          text: az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --account-type Standard_LRS
          max_profile: 2017-03-09-profile
"""

helps['storage container create'] = """
    type: command
    short-summary: Create a container in a storage account.
    examples:
        - name: Create a storage container in a storage account.
          text: az storage container create -n MyStorageContainer
        - name: Create a storage container in a storage account and return an error if the container already exists.
          text: az storage container create -n MyStorageContainer --fail-on-exist
"""

helps['storage account list'] = """
    type: command
    short-summary: List storage accounts.
    examples:
        - name: List all storage accounts in a subscription.
          text: az storage account list
        - name: List all storage accounts in a resource group.
          text: az storage account list -g MyResourceGroup
"""

helps['storage account show'] = """
    type: command
    short-summary: Show storage account properties.
    examples:
        - name: Show properties for a storage account by resource ID.
          text: az storage account show --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Storage/storageAccounts/{StorageAccount}
        - name: Show properties for a storage account using an account name and resource group.
          text: az storage account show -g MyResourceGroup -n MyStorageAccount
"""

helps['storage account show-usage'] = """
    type: command
    short-summary: Show the current count and limit of the storage accounts under the subscription.
"""

helps['storage blob list'] = """
    type: command
    short-summary: List storage blobs in a container.
    examples:
        - name: List all storage blobs in a container.
          text: az storage blob list -c MyContainer
"""

helps['storage account delete'] = """
    type: command
    short-summary: Delete a storage account.
    examples:
        - name: Delete a storage account using a resource ID.
          text: az storage account delete --ids /subscriptions/{SubID}/resourceGroups/{ResourceGroup}/providers/Microsoft.Storage/storageAccounts/{StorageAccount}
        - name: Delete a storage account using an account name and resource group.
          text: az storage account delete -n MyStorageAccount -g MyResourceGroup
"""

helps['storage account show-connection-string'] = """
    type: command
    short-summary: Get the connection string for a storage account.
    examples:
        - name: Get a connection string for a storage account.
          text: az storage account show-connection-string -g MyResourceGroup -n MyStorageAccount
"""

helps['storage'] = """
    type: group
    short-summary: Manage Azure Cloud Storage resources.
"""

helps['storage account'] = """
    type: group
    short-summary: Manage storage accounts.
"""

helps['storage account update'] = """
    type: command
    short-summary: Update the properties of a storage account.
"""

helps['storage account keys'] = """
    type: group
    short-summary: Manage storage account keys.
"""

helps['storage account keys list'] = """
    type: command
    short-summary: List the primary and secondary keys for a storage account.
    examples:
        - name: List the primary and secondary keys for a storage account.
          text: az storage account keys list -g MyResourceGroup -n MyStorageAccount
"""

helps['storage blob'] = """
    type: group
    short-summary: Manage object storage for unstructured data (blobs).
"""

helps['storage blob exists'] = """
    type: command
    short-summary: Check for the existence of a blob in a container.
    parameters:
        - name: --name -n
          short-summary: The blob name.
"""

helps['storage blob list'] = """
    type: command
    short-summary: List blobs in a given container.
    parameters:
        - name: --include
          short-summary: 'Specifies additional datasets to include: (c)opy-info, (m)etadata, (s)napshots, (d)eleted-soft. Can be combined.'
"""

helps['storage blob copy'] = """
    type: group
    short-summary: Manage blob copy operations.
"""

helps['storage blob incremental-copy'] = """
    type: group
    short-summary: Manage blob incremental copy operations.
"""

helps['storage blob lease'] = """
    type: group
    short-summary: Manage storage blob leases.
"""

helps['storage blob metadata'] = """
    type: group
    short-summary: Manage blob metadata.
"""

helps['storage blob service-properties'] = """
    type: group
    short-summary: Manage storage blob service properties.
"""

helps['storage blob service-properties delete-policy'] = """
    type: group
    short-summary: Manage storage blob delete-policy service properties.
"""
helps['storage blob service-properties delete-policy show'] = """
    type: command
    short-summary: Show the storage blob delete-policy.
"""
helps['storage blob service-properties delete-policy update'] = """
    type: command
    short-summary: Update the storage blob delete-policy.
"""

helps['storage blob set-tier'] = """
    type: command
    short-summary: Set the block or page tiers on the blob.
    parameters:
        - name: --type -t
          short-summary: The blob type
        - name: --tier
          short-summary: The tier value to set the blob to.
        - name: --timeout
          short-summary: The timeout parameter is expressed in seconds. This method may make multiple calls to
                         the Azure service and the timeout will apply to each call individually.
    long-summary:  >
        For block blob this command only supports block blob on standard storage accounts.
        For page blob, this command only supports for page blobs on premium accounts.
"""

helps['storage blob upload-batch'] = """
    type: command
    short-summary: Upload files from a local directory to a blob container.
    parameters:
        - name: --source -s
          type: string
          short-summary: The directory where the files to be uploaded are located.
        - name: --destination -d
          type: string
          short-summary: The blob container where the files will be uploaded.
          long-summary: The destination can be the container URL or the container name. When the destination is the container URL, the storage
                        account name will be parsed from the URL.
        - name: --pattern
          type: string
          short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq]', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: Show the summary of the operations to be taken instead of actually uploading the file(s).
        - name: --if-match
          type: string
          short-summary: An ETag value, or the wildcard character (*). Specify this header to perform the operation
                         only if the resource's ETag matches the value specified.
        - name: --if-none-match
          type: string
          short-summary: An ETag value, or the wildcard character (*).
          long-summary: Specify this header to perform the operation only if the resource's ETag does not match the value specified.
                        Specify the wildcard character (*) to perform the operation only if the resource does not exist, and fail the operation if it does exist.
        - name: --validate-content
          short-summary: Specifies that an MD5 hash shall be calculated for each chunk of the blob and verified by the
                         service when the chunk has arrived.
        - name: --type -t
          short-summary: Defaults to 'page' for *.vhd files, or 'block' otherwise. The setting will override blob types
                         for every file.
        - name: --maxsize-condition
          short-summary: The max length in bytes permitted for an append blob.
        - name: --lease-id
          short-summary: Required if the blob has an active lease
"""

helps['storage blob download-batch'] = """
    type: command
    short-summary: Download blobs from a blob container recursively.
    parameters:
        - name: --source -s
          type: string
          short-summary: The blob container from where the files will be downloaded.
          long-summary: The source can be the container URL or the container name. When the source is the container URL, the storage
                        account name will be parsed from the URL.
        - name: --destination -d
          type: string
          short-summary: The existing destination folder for this download operation.
        - name: --pattern
          type: string
          short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq]', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: Show the summary of the operations to be taken instead of actually downloading the file(s).
"""

helps['storage blob delete-batch'] = """
    type: command
    short-summary: Delete blobs from a blob container recursively.
    parameters:
        - name: --source -s
          type: string
          short-summary: The blob container from where the files will be deleted.
          long-summary: The source can be the container URL or the container name. When the source is the container URL, the storage
                        account name will be parsed from the URL.
        - name: --pattern
          type: string
          short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq]', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: Show the summary of the operations to be taken instead of actually deleting the file(s).
        - name: --if-match
          type: string
          short-summary: An ETag value, or the wildcard character (*). Specify this header to perform the operation
                         only if the resource's ETag matches the value specified.
        - name: --if-none-match
          type: string
          short-summary: An ETag value, or the wildcard character (*).
          long-summary: Specify this header to perform the operation only if the resource's ETag does not match the value specified.
                        Specify the wildcard character (*) to perform the operation only if the resource does not exist, and fail the operation if it does exist.

"""

helps['storage blob copy start-batch'] = """
    type: command
    short-summary: Copy multiple blobs or files to a blob container.
    parameters:
        - name: --destination-container
          type: string
          short-summary: The blob container where the selected source files or blobs will be copied to.
        - name: --pattern
          type: string
          short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: List the files or blobs to be uploaded. No actual data transfer will occur.
        - name: --source-account-name
          type: string
          short-summary: The source storage account from which the files or blobs are copied to the destination. If omitted, the source account is used.
        - name: --source-account-key
          type: string
          short-summary: The account key for the source storage account.
        - name: --source-container
          type: string
          short-summary: The source container from which blobs are copied.
        - name: --source-share
          type: string
          short-summary: The source share from which files are copied.
        - name: --source-uri
          type: string
          short-summary: A URI specifying a file share or blob container from which the files or blobs are copied.
          long-summary: If the source is in another account, the source must either be public or be authenticated by using a shared access signature.
        - name: --source-sas
          type: string
          short-summary: The shared access signature for the source storage account.
"""

helps['storage container'] = """
    type: group
    short-summary: Manage blob storage containers.
"""

helps['storage container exists'] = """
    type: command
    short-summary: Check for the existence of a storage container.
"""

helps['storage container list'] = """
    type: command
    short-summary: List containers in a storage account.
"""

helps['storage container lease'] = """
    type: group
    short-summary: Manage blob storage container leases.
"""

helps['storage container metadata'] = """
    type: group
    short-summary: Manage container metadata.
"""

helps['storage container policy'] = """
    type: group
    short-summary: Manage container stored access policies.
"""

helps['storage cors'] = """
    type: group
    short-summary: Manage storage service Cross-Origin Resource Sharing (CORS).
"""

helps['storage cors add'] = """
    type: command
    short-summary: Add a CORS rule to a storage account.
    parameters:
        - name: --services
          short-summary: >
            The storage service(s) to add rules to. Allowed options are: (b)lob, (f)ile,
            (q)ueue, (t)able. Can be combined.
        - name: --max-age
          short-summary: The maximum number of seconds the client/browser should cache a preflight response.
        - name: --origins
          short-summary: Space-separated list of origin domains that will be allowed via CORS, or '*' to allow all
                         domains.
        - name: --methods
          short-summary: Space-separated list of HTTP methods allowed to be executed by the origin.
        - name: --allowed-headers
          short-summary: Space-separated list of response headers allowed to be part of the cross-origin request.
        - name: --exposed-headers
          short-summary: Space-separated list of response headers to expose to CORS clients.
"""

helps['storage cors clear'] = """
    type: command
    short-summary: Remove all CORS rules from a storage account.
    parameters:
        - name: --services
          short-summary: >
            The storage service(s) to remove rules from. Allowed options are: (b)lob, (f)ile,
            (q)ueue, (t)able. Can be combined.
"""

helps['storage cors list'] = """
    type: command
    short-summary: List all CORS rules for a storage account.
    parameters:
        - name: --services
          short-summary: >
            The storage service(s) to list rules for. Allowed options are: (b)lob, (f)ile,
            (q)ueue, (t)able. Can be combined.
"""

helps['storage directory'] = """
    type: group
    short-summary: Manage file storage directories.
"""

helps['storage directory exists'] = """
    type: command
    short-summary: Check for the existence of a storage directory.
"""

helps['storage directory metadata'] = """
    type: group
    short-summary: Manage file storage directory metadata.
"""

helps['storage directory list'] = """
    type: command
    short-summary: List directories in a share.
"""

helps['storage entity'] = """
    type: group
    short-summary: Manage table storage entities.
"""

helps['storage entity query'] = """
    type: command
    short-summary: List entities which satisfy a query.
"""

helps['storage file'] = """
    type: group
    short-summary: Manage file shares that use the SMB 3.0 protocol.
"""

helps['storage file exists'] = """
    type: command
    short-summary: Check for the existence of a file.
"""

helps['storage file list'] = """
    type: command
    short-summary: List files and directories in a share.
    parameters:
        - name: --exclude-dir
          type: bool
          short-summary: List only files in the given share.
"""

helps['storage file copy'] = """
    type: group
    short-summary: Manage file copy operations.
"""

helps['storage file metadata'] = """
    type: group
    short-summary: Manage file metadata.
"""

helps['storage file upload-batch'] = """
    type: command
    short-summary: Upload files from a local directory to an Azure Storage File Share in a batch operation.
    parameters:
        - name: --source -s
          type: string
          short-summary: The directory to upload files from.
        - name: --destination -d
          type: string
          short-summary: The destination of the upload operation.
          long-summary: The destination can be the file share URL or the share name. When the destination is the share URL, the storage account name is parsed from the URL.
        - name: --destination-path
          type: string
          short-summary: The directory where the source data is copied to. If omitted, data is copied to the root directory.
        - name: --pattern
          type: string
          short-summary: The pattern used for file globbing. The supported patterns are '*', '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: List the files and blobs to be uploaded. No actual data transfer will occur.
        - name: --max-connections
          type: integer
          short-summary: The maximum number of parallel connections to use. Default value is 1.
        - name: --validate-content
          type: bool
          short-summary: If set, calculates an MD5 hash for each range of the file for validation.
          long-summary: >
            The storage service checks the hash of the content that has arrived is identical to the hash that was sent.
            This is mostly valuable for detecting bitflips during transfer if using HTTP instead of HTTPS. This hash is not stored.
"""

helps['storage file download-batch'] = """
    type: command
    short-summary: Download files from an Azure Storage File Share to a local directory in a batch operation.
    parameters:
        - name: --source -s
          type: string
          short-summary: The source of the file download operation. The source can be the file share URL or the share name.
        - name: --destination -d
          type: string
          short-summary: The local directory where the files are downloaded to. This directory must already exist.
        - name: --pattern
          type: string
          short-summary: The pattern used for file globbing. The supported patterns are '*', '?', '[seq]', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: List the files and blobs to be downloaded. No actual data transfer will occur.
        - name: --max-connections
          type: integer
          short-summary: The maximum number of parallel connections to use. Default value is 1.
        - name: --validate-content
          type: bool
          short-summary: If set, calculates an MD5 hash for each range of the file for validation.
          long-summary: >
            The storage service checks the hash of the content that has arrived is identical to the hash that was sent.
            This is mostly valuable for detecting bitflips during transfer if using HTTP instead of HTTPS. This hash is not stored.
"""

helps['storage file delete-batch'] = """
    type: command
    short-summary: Delete files from an Azure Storage File Share.
    parameters:
        - name: --source -s
          type: string
          short-summary: The source of the file delete operation. The source can be the file share URL or the share name.
        - name: --pattern
          type: string
          short-summary: The pattern used for file globbing. The supported patterns are '*', '?', '[seq]', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: List the files and blobs to be deleted. No actual data deletion will occur.
"""

helps['storage file copy start-batch'] = """
    type: command
    short-summary: Copy multiple files or blobs to a file share.
    parameters:
        - name: --destination-share
          type: string
          short-summary: The file share where the source data is copied to.
        - name: --destination-path
          type: string
          short-summary: The directory where the source data is copied to. If omitted, data is copied to the root directory.
        - name: --pattern
          type: string
          short-summary: The pattern used for globbing files and blobs. The supported patterns are '*', '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: List the files and blobs to be copied. No actual data transfer will occur.
        - name: --source-account-name
          type: string
          short-summary: The source storage account to copy the data from. If omitted, the destination account is used.
        - name: --source-account-key
          type: string
          short-summary: The account key for the source storage account. If omitted, the active login is used to determine the account key.
        - name: --source-container
          type: string
          short-summary: The source container blobs are copied from.
        - name: --source-share
          type: string
          short-summary: The source share files are copied from.
        - name: --source-uri
          type: string
          short-summary: A URI that specifies a the source file share or blob container.
          long-summary: If the source is in another account, the source must either be public or authenticated via a shared access signature.
        - name: --source-sas
          type: string
          short-summary: The shared access signature for the source storage account.
"""

helps['storage logging'] = """
    type: group
    short-summary: Manage storage service logging information.
"""

helps['storage logging show'] = """
    type: command
    short-summary: Show logging settings for a storage account.
    parameters:
        - name: --services
          short-summary: 'The storage services from which to retrieve logging info: (b)lob (q)ueue (t)able. Can be
                         combined.'
"""

helps['storage logging update'] = """
    type: command
    short-summary: Update logging settings for a storage account.
    parameters:
        - name: --services
          short-summary: 'The storage service(s) for which to update logging info: (b)lob (q)ueue (t)able. Can be
                         combined.'
        - name: --log
          short-summary: 'The operations for which to enable logging: (r)ead (w)rite (d)elete. Can be combined.'
        - name: --retention
          short-summary: Number of days for which to retain logs. 0 to disable.
"""

helps['storage message'] = """
    type: group
    short-summary: Manage queue storage messages.
"""

helps['storage metrics'] = """
    type: group
    short-summary: Manage storage service metrics.
"""

helps['storage metrics show'] = """
    type: command
    short-summary: Show metrics settings for a storage account.
    parameters:
        - name: --services
          short-summary: 'The storage services from which to retrieve metrics info: (b)lob (q)ueue (t)able. Can be
                         combined.'
        - name: --interval
          short-summary: Filter the set of metrics to retrieve by time interval
"""

helps['storage metrics update'] = """
    type: command
    short-summary: Update metrics settings for a storage account.
    parameters:
        - name: --services
          short-summary: 'The storage services from which to retrieve metrics info: (b)lob (q)ueue (t)able. Can be
                         combined.'
        - name: --hour
          short-summary: Update the hourly metrics
        - name: --minute
          short-summary: Update the by-minute metrics
        - name: --api
          short-summary: Specify whether to include API in metrics. Applies to both hour and minute metrics if both are
                         specified. Must be specified if hour or minute metrics are enabled and being updated.
        - name: --retention
          short-summary: Number of days for which to retain metrics. 0 to disable. Applies to both hour and minute
                         metrics if both are specified.
"""

helps['storage queue'] = """
    type: group
    short-summary: Manage storage queues.
"""

helps['storage queue list'] = """
    type: command
    short-summary: List queues in a storage account.
"""

helps['storage queue metadata'] = """
    type: group
    short-summary: Manage the metadata for a storage queue.
"""

helps['storage queue policy'] = """
    type: group
    short-summary: Manage shared access policies for a storage queue.
"""

helps['storage share'] = """
    type: group
    short-summary: Manage file shares.
"""

helps['storage share exists'] = """
    type: command
    short-summary: Check for the existence of a file share.
"""

helps['storage share list'] = """
    type: command
    short-summary: List the file shares in a storage account.
"""

helps['storage share metadata'] = """
    type: group
    short-summary: Manage the metadata of a file share.
"""

helps['storage share policy'] = """
    type: group
    short-summary: Manage shared access policies of a storage file share.
"""

helps['storage table'] = """
    type: group
    short-summary: Manage NoSQL key-value storage.
"""

helps['storage table list'] = """
    type: command
    short-summary: List tables in a storage account.
"""

helps['storage table policy'] = """
    type: group
    short-summary: Manage shared access policies of a storage table.
"""

helps['storage account network-rule'] = """
    type: group
    short-summary: Manage network rules.
"""

helps['storage account network-rule add'] = """
    type: command
    short-summary: Add a network rule.
    long-summary: >
        Rules can be created for an IPv4 address, address range (CIDR format), or a virtual network subnet.
    examples:
        - name: Create a rule to allow a specific address-range.
          text: az storage account network-rule add -g myRg --account-name mystorageaccount --ip-address 23.45.1.0/24
        - name: Create a rule to allow access for a subnet.
          text: az storage account network-rule add -g myRg --account-name mystorageaccount --vnet myvnet --subnet mysubnet
"""

helps['storage account network-rule list'] = """
    type: command
    short-summary: List network rules.
"""

helps['storage account network-rule remove'] = """
    type: command
    short-summary: Remove a network rule.
"""

helps['storage account generate-sas'] = """
    type: command
    parameters:
        - name: --services
          short-summary: 'The storage services the SAS is applicable for. Allowed values: (b)lob (f)ile (q)ueue (t)able.
                         Can be combined.'
        - name: --resource-types
          short-summary: 'The resource types the SAS is applicable for. Allowed values: (s)ervice (c)ontainer (o)bject.
                         Can be combined.'
        - name: --expiry
          short-summary: Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes invalid.
        - name: --start
          short-summary: Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes valid. Defaults to the
                         time of the request.
        - name: --account-name
          short-summary: 'Storage account name. Must be used in conjunction with either storage account key or a SAS
                         token. Environment Variable: AZURE_STORAGE_ACCOUNT'
"""
