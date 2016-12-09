# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long, too-many-lines

helps['storage entity insert'] = """
    type: command
    short-summary: Insert a new entity into the table.
    long-summary: Inserts a new entity into the table. When inserting an entity into a table, you must specify values for the PartitionKey and RowKey system properties. Together, these properties form the primary key and must be unique within the table. Both the PartitionKey and RowKey values may be up to 64 KB in size. If you are using an integer value as a key, you should convert the integer to a fixed-width string, because they are canonically sorted. For example, you should convert the value 1 to 0000001 to ensure proper sorting.
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

helps['storage'] = """
    type: group
    short-summary: Durable, highly available, and massively scalable cloud storage
"""

helps['storage account'] = """
    type: group
    short-summary: Manage storage accounts.
"""

helps['storage account keys'] = """
    type: group
    short-summary: Manage storage account keys.
"""

helps['storage blob'] = """
    type: group
    short-summary: Object storage for unstructured data
"""

helps['storage blob exists'] = """
    type: command
    short-summary: Returns a boolean indicating whether the blob exists.
"""

helps['storage blob list'] = """
    type: command
    short-summary: List blobs in a given container.
"""

helps['storage blob copy'] = """
    type: group
    short-summary: Manage blob copy operations.
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

helps['storage container'] = """
    type: group
    short-summary: Manage blob storage containers.
"""

helps['storage container exists'] = """
    type: command
    short-summary: Returns a boolean indicating whether the container exists.
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
    short-summary: Manage Storage service Cross-Orgin Resource Sharing (CORS)
"""

helps['storage cors add'] = """
    type: command
    short-summary: Add a CORS rule to a storage account.
"""

helps['storage cors clear'] = """
    type: command
    short-summary: Remove all CORS rules from a storage account.
"""

helps['storage cors list'] = """
    type: command
    short-summary: List all CORS rules for a storage account.
"""

helps['storage directory'] = """
    type: group
    short-summary: Manage file storage directories.
"""

helps['storage directory exists'] = """
    type: command
    short-summary: Returns a boolean indicating whether the directory exists.
"""

helps['storage directory metadata'] = """
    type: group
    short-summary: Manage file storage directory metadata.
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
    short-summary: File shares that use the standard SMB 3.0 protocol
"""

helps['storage file exists'] = """
    type: command
    short-summary: Returns a boolean indicating whether the file exists.
"""

helps['storage file list'] = """
    type: command
    short-summary: List files and directories in the specified share.
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
    short-summary: Upload files from local directory to Azure Storage File Share in batch
    parameters:
        - name: --source -s
          type: string
          short-summary: The directory from which the files should to be uploaded.
        - name: --destination -d
          type: string
          short-summary: The string represents the destination of this upload operation. The
                         destination can be the file share URL or the share name. When the 
                         destination is the share URL, the storage account name will parsed
                         from the URL.
        - name: --pattern
          type: string
          short-summary: The pattern is used for files globbing. The supported patterns are '*',
                         '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: Output the list of files which would be uploaded. No actual data transfer
                         will occur.
        - name: --max-connections
          type: integer
          short-summary: Maximum number of parallel connections to use. Default value is 1.
        - name: --validate-content
          type: bool
          short-summary: If set, calculates an MD5 hash for each range of the file. The storage
                         service checks the hash of the content that has arrived with the hash that
                         was sent. This is primarily valuable for detecting bitflips on the wire if
                         using http instead of https as https (the default) will already validate.
                         Note that this MD5 hash is not stored with the file.
"""

helps['storage file download-batch'] = """
    type: command
    short-summary: Download files from Azure Storage File Share to a local directory in batch
    parameters:
        - name: --source -s
          type: string
          short-summary: The string represents the source of this file download operation. The
                         source can be the file share URL or the share name. When the source is
                         the share URL, the storage account name will parsed from the URL.
        - name: --destination -d
          type: string
          short-summary: The directory where the files to be downloaded. The directory must exist.
        - name: --pattern
          type: string
          short-summary: The pattern is used for files globbing. The supported patterns are '*',
                         '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: Output the list of files which would be downloaded. No actual data transfer
                         will occur.
        - name: --max-connections
          type: integer
          short-summary: Maximum number of parallel connections to use. Default value is 1.
        - name: --validate-content
          type: bool
          short-summary: If set, calculates an MD5 hash for each range of the file. The storage
                         service checks the hash of the content that has arrived with the hash that
                         was sent. This is primarily valuable for detecting bitflips on the wire if
                         using http instead of https as https (the default) will already validate.
                         Note that this MD5 hash is not stored with the file.
"""

helps['storage file copy start-batch'] = """
    type: command
    short-summary: Copy multiple files to file share asynchronously.
    parameters:
        - name: --destination-share
          type: string
          short-summary: The file share where the specified source files or blobs to be copied to.
        - name: --destination-path
          type: string
          short-summary: The directory where the specified source files or blobs to be copied to. If
                         omitted, the files or blobs will be copied to the root directory.
        - name: --pattern
          type: string
          short-summary: The pattern is used for globbing files or blobs in the source. The
                         supported patterns are '*', '?', '[seq', and '[!seq]'.
        - name: --dryrun
          type: bool
          short-summary: Output the list of files or blobs which would be uploaded. No actual data
                         transfer will occur.
        - name: --source-account
          type: string
          short-summary: The source storage account from which the files or blobs will be copied to
                         the destination. If omitted, it is assumed that source is in the same
                         storage account as destination
        - name: --source-key
          type: string
          short-summary: The account key for the source storage account.
        - name: --source-container
          type: string
          short-summary: The source container from which the blobs will be copied to the destination
        - name: --source-share
          type: string
          short-summary: The source share from which the files will be copied to the destination
        - name: --source-uri
          type: string
          short-summary: A URI specifies an file share or blob container from which the files or
                         blobs will be copied to the destination. If the source is in another
                         account, the source must either be public or must be authenticated via a
                         shared access signature. If the source is public, no authentication is
                         required.
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
    short-summary: Effectively scale apps according to traffic using queues.
"""

helps['storage queue list'] = """
    type: command
    short-summary: List queues in a storage account.
"""

helps['storage queue metadata'] = """
    type: group
    short-summary: Manage storage queue metadata.
"""

helps['storage queue policy'] = """
    type: group
    short-summary: Manage storage queue shared access policies.
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
    short-summary: Manage file share metadata.
"""

helps['storage share policy'] = """
    type: group
    short-summary: Manage storage file share shared access policies.
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
    short-summary: Manage storage table shared access policies.
"""
