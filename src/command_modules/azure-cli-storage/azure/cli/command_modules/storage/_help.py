# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long, too-many-lines

helps['storage entity insert'] = """
    type: command
    short-summary: Insert an entity into the table.
    long-summary: Inserts an entity into the table. When inserting an entity into a table, you must specify values for the PartitionKey and RowKey system properties. Together, these properties form the primary key and must be unique within the table. Both the PartitionKey and RowKey values may be up to 64 KB in size. If you are using an integer value as a key, you should convert the integer to a fixed-width string, because they are canonically sorted. For example, you should convert the value 1 to 0000001 to ensure proper sorting.
    parameters:
        - name: --table-name -t
          type: string
          short-summary: 'The name of the table to insert the entity into.'
        - name: --entity -e
          type: list
          short-summary: 'A space-separated list of key=value pairs. Must contain a PartitionKey and a RowKey.'
        - name: --if-exists
          type: string
          short-summary: 'Specify what should happen if an entity already exists for the specified PartitionKey and RowKey.'
        - name: --timeout
          short-summary: The server timeout, expressed in seconds.
"""

helps['storage blob upload'] = """
    type: command
    short-summary: Upload a specified file to a storage blob.
    long-summary: Creates a new blob from a file path, or updates the content of an existing blob, with automatic chunking and progress notifications.
    examples:
        - name: Upload to a blob with all required fields.
          text: az storage blob upload -f /path/to/file -c MyContainer -n MyBlob
"""

helps['storage file upload'] = """
    type: command
    short-summary: Upload a specified file to a file share that uses the standard SMB 3.0 protocol
    long-summary: Creates or updates an azure file from a source path with automatic chunking and progress notifications.
    examples:
        - name: Upload to a file share with all required fields.
          text: az storage file upload -s MyShare -source /path/to/file
"""

helps['storage blob show'] = """
    type: command
    short-summary: Returns properties for a named blob in a container in a storage account.
    long-summary: Blob properties only.  To show contents of a blob, use az storage blob list
    examples:
        - name: Show properties of a blob with all required fields.
          text: az storage blob show -c MyContainer -n MyBlob
"""

helps['storage blob delete'] = """
    type: command
    short-summary: Marks the specified blob or snapshot for deletion.
    long-summary: The blob is marked for later deletion during garbage collection.  Note that in order to delete a blob, you must delete all of its snapshots. You can delete both at the same time with the Delete Blob operation.
    examples:
        - name: Delete a blob with all required fields.
          text: az storage blob delete -c MyContainer -n MyBlob
"""

helps['storage account create'] = """
    type: command
    short-summary: Creates a storage account.
    examples:
        - name: Create a storage account MyStorageAccount in resource group MyResourceGroup in the West US region with locally redundant storage.
          text: az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --sku Standard_LRS
          min_profile: latest
        - name: Create a storage account MyStorageAccount in resource group MyResourceGroup in the West US region with locally redundant storage.
          text: az storage account create -n MyStorageAccount -g MyResourceGroup -l westus --account-type Standard_LRS
          max_profile: 2017-03-09-profile-preview
"""

helps['storage container create'] = """
    type: command
    short-summary: Creates a container in a storage account.
    examples:
        - name: Create a storage container in a storage account.
          text: az storage container create -n MyStorageContainer
        - name: Create a storage container in a storage account and return an error if the container already exists.
          text: az storage container create -n MyStorageContainer --fail-on-exist
"""

helps['storage account list'] = """
    type: command
    short-summary: Lists storage accounts
    examples:
        - name: List all storage accounts in a subscription.
          text: az storage account list
        - name: List all storage accounts in a region.
          text: az storage account list -g MyResourceGroup
"""

helps['storage account show'] = """
    type: command
    short-summary: Returns storage account properties
    examples:
        - name: Show properties for a storage account using one or more resource ID.
          text: az storage account show --ids ${storage_account_resource_id}
        - name: Show properties for a storage account using an account name and resource group.
          text: az storage account show -g MyResourceGroup -n MyStorageAccount
"""

helps['storage blob list'] = """
    type: command
    short-summary: Lists storage blobs in a container.
    examples:
        - name: List all storage blobs in a container.
          text: az storage blob list -c MyContainer
"""

helps['storage account delete'] = """
    type: command
    short-summary: Deletes a storage account.
    examples:
        - name: Delete a storage account using one or more resource ID.
          text: az storage account delete --ids ${storage_account_resource_id}
        - name: Delete a storage account using an account name and resource group.
          text: az storage account delete -n MyStorageAccount -g MyResourceGroup
"""


helps['storage account show-connection-string'] = """
    type: command
    short-summary: Returns the properties for the specified storage account.
    examples:
        - name: Get a connection string for a storage account.
          text: az storage account show-connection-string -g MyResourceGroup -n MyStorageAccount
"""

helps['storage'] = """
    type: group
    short-summary: Durable, highly available, and massively scalable cloud storage.
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
    short-summary: Lists the primary and secondary keys for a storage account.
    examples:
        - name: List the primary and secondary keys for a storage account.
          text: az storage account keys list -g MyResourceGroup -n MyStorageAccount
"""

helps['storage blob'] = """
    type: group
    short-summary: Object storage for unstructured data.
"""

helps['storage blob exists'] = """
    type: command
    short-summary: Indicates whether the blob exists.
"""

helps['storage blob list'] = """
    type: command
    short-summary: List blobs in a given container.
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
helps['storage blob copy start-batch'] = """
    type: command
    short-summary: Copy multiple blobs or files to a blob container.
    parameters:
        - name: --destination-container
          type: string
          short-summary: The blob container where the selected source files or blobs to be copied to.
        - name: --pattern
          type: string
          short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: List of files or blobs to be uploaded. No actual data transfer will occur.
        - name: --source-account-name
          type: string
          short-summary: The source storage account from which the files or blobs are copied to the destination. If omitted, it is assumed that source is in the same storage account as destination.
        - name: --source-account-key
          type: string
          short-summary: The account key for the source storage account.
        - name: --source-container
          type: string
          short-summary: The source container from which the blobs are copied to the destination.
        - name: --source-share
          type: string
          short-summary: The source share from which the files are copied to the destination.
        - name: --source-uri
          type: string
          short-summary: A URI specifies an file share or blob container from which the files or blobs are copied to the destination. If the source is in another account, the source must either be public or must be authenticated by using a shared access signature. If the source is public, no authentication is required.
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
    short-summary: Indicates whether the container exists.
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
    short-summary: Manage Storage service Cross-Origin Resource Sharing (CORS).
"""

helps['storage cors add'] = """
    type: command
    short-summary: Add a CORS rule to a storage account.
    parameters:
        - name: --services
          short-summary: The storage service(s) for which to add the CORS rules. Allowed options are (b)lob (f)ile
                         (q)ueue (t)able. Can be combined.
        - name: --max-age
          short-summary: The number of seconds the client/browser should cache a preflight response.
        - name: --origins
          short-summary: List of origin domains that will be allowed via CORS, or "*" to allow all domains.
        - name: --methods
          short-summary: List of HTTP methods allowed to be executed by the origin.
        - name: --allowed-headers
          short-summary: List of response headers allowed to be part of the cross-origin request.
        - name: --exposed-headers
          short-summary: List of response headers to expose to CORS clients.
"""

helps['storage cors clear'] = """
    type: command
    short-summary: Remove all CORS rules from a storage account.
    parameters:
        - name: --services
          short-summary: The storage service(s) for which to add the CORS rules. Allowed options are (b)lob (f)ile
                         (q)ueue (t)able. Can be combined.
"""

helps['storage cors list'] = """
    type: command
    short-summary: List all CORS rules for a storage account.
    parameters:
        - name: --services
          short-summary: The storage service(s) for which to add the CORS rules. Allowed options are (b)lob (f)ile
                         (q)ueue (t)able. Can be combined.
"""

helps['storage directory'] = """
    type: group
    short-summary: Manage file storage directories.
"""

helps['storage directory exists'] = """
    type: command
    short-summary: Indicates whether the directory exists.
"""

helps['storage directory metadata'] = """
    type: group
    short-summary: Manage file storage directory metadata.
"""

helps['storage directory list'] = """
    type: command
    short-summary: List directories in the specified share.
"""

helps['storage entity'] = """
    type: group
    short-summary: Manage table storage entities.
"""

helps['storage entity query'] = """
    type: command
    short-summary: List entities which satisfy a given query.
"""


helps['storage file'] = """
    type: group
    short-summary: File shares that use the standard SMB 3.0 protocol.
"""

helps['storage file exists'] = """
    type: command
    short-summary: Indicates whether the file exists.
"""

helps['storage file list'] = """
    type: command
    short-summary: List files and directories in the specified share.
    parameters:
        - name: --exclude-dir
          type: bool
          short-summary: List only files in the specified share.
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
    short-summary: Upload files from a local directory to an Azure Storage File Share in batch.
    parameters:
        - name: --source -s
          type: string
          short-summary: The directory from which the files should be uploaded.
        - name: --destination -d
          type: string
          short-summary: The destination of the upload operation. The destination can be the file share URL or the share name. When the destination is the share URL, the storage account name is parsed from the URL.
        - name: --pattern
          type: string
          short-summary: The pattern used for file globbing. The supported patterns are '*', '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: The list of files to upload. No actual data transfer occurs.
        - name: --max-connections
          type: integer
          short-summary: The maximum number of parallel connections to use. Default value is 1.
        - name: --validate-content
          type: bool
          short-summary: If set, calculates an MD5 hash for each range of the file. The Storage service checks the hash of the content that has arrived with the hash that was sent. This is primarily valuable for detecting bitflips on the wire if using http instead of https as https (the default) will already validate. Note that this MD5 hash is not stored with the file.
"""

helps['storage file download-batch'] = """
    type: command
    short-summary: Download files from an Azure Storage File Share to a local directory in batch.
    parameters:
        - name: --source -s
          type: string
          short-summary: The source of the file download operation. The source can be the file share URL or the share name. When the source is the share URL, the storage account name is parsed from the URL.
        - name: --destination -d
          type: string
          short-summary: The directory where the files are downloaded. The directory must exist.
        - name: --pattern
          type: string
          short-summary: The pattern used for file globbing. The supported patterns are '*', '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: The list of files to be downloaded. No actual data transfer occurs.
        - name: --max-connections
          type: integer
          short-summary: The maximum number of parallel connections to use. Default value is 1.
        - name: --validate-content
          type: bool
          short-summary: If set, calculates an MD5 hash for each range of the file. The Storage service checks the hash of the content that has arrived with the hash that was sent. This is primarily valuable for detecting bitflips on the wire if using http instead of https as https (the default) will already validate. Note that this MD5 hash is not stored with the file.
"""

helps['storage file copy start-batch'] = """
    type: command
    short-summary: Copy multiple files or blobs to a file share.
    parameters:
        - name: --destination-share
          type: string
          short-summary: The file share where the specified source files or blobs are to be copied to.
        - name: --destination-path
          type: string
          short-summary: The directory where the specified source files or blobs are to be copied to. If omitted, the files or blobs are copied to the root directory.
        - name: --pattern
          type: string
          short-summary: The pattern used for globbing files or blobs in the source. The supported patterns are '*', '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool

          short-summary: The list of files or blobs to be uploaded. No actual data transfer occurs.
        - name: --source-account-name
          type: string
          short-summary: The source storage account from which the files or blobs are copied to the destination. If omitted, it is assumed that source is in the same storage account as destination.
        - name: --source-account-key
          type: string
          short-summary: The account key for the source storage account. If it is omitted, the command will try to query the key using the current log in.
        - name: --source-container
          type: string
          short-summary: The source container from which the blobs are copied to the destination.
        - name: --source-share
          type: string
          short-summary: The source share from which the files are copied to the destination.
        - name: --source-uri
          type: string
          short-summary: A URI that specifies a file share or blob container from which files or blobs are copied to the destination. If the source is in another account, the source must either be public or must be authenticated via a shared access signature. If the source is public, no authentication is required.
        - name: --source-sas
          type: string
          short-summary: The shared access signature for the source storage account.
"""

helps['storage logging'] = """
    type: group
    short-summary: Manage Storage service logging information.
"""

helps['storage logging show'] = """
    type: command
    short-summary: Show logging settings for a storage account.
"""

helps['storage logging update'] = """
    type: command
    short-summary: Update logging settings for a storage account.
"""

helps['storage message'] = """
    type: group
    short-summary: Manage queue storage messages.
"""

helps['storage metrics'] = """
    type: group
    short-summary: Manage Storage service metrics.
"""

helps['storage metrics show'] = """
    type: command
    short-summary: Show metrics settings for a storage account.
"""

helps['storage metrics update'] = """
    type: command
    short-summary: Update metrics settings for a storage account.
"""

helps['storage queue'] = """
    type: group
    short-summary: Use queues to effectively scale applications according to traffic.
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
    short-summary: Returns a boolean indicating whether the share exists.
"""

helps['storage share list'] = """
    type: command
    short-summary: List file shares in a storage account.
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
    short-summary: NoSQL key-value storage using semi-structured datasets.
"""

helps['storage table list'] = """
    type: command
    short-summary: List tables in a storage account.
"""

helps['storage table policy'] = """
    type: group
    short-summary: Manage shared access policies of a storage table.
"""
