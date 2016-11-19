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

helps['storage directory'] = """
    type: group
    short-summary: Manage file storage directories.
"""

helps['storage directory metadata'] = """
    type: group
    short-summary: Manage file storage directory metadata.
"""

helps['storage entity'] = """
    type: group
    short-summary: Manage table storage entities.
"""

helps['storage file'] = """
    type: group
    short-summary: File shares that use the standard SMB 3.0 protocol
"""

helps['storage file copy'] = """
    type: group
    short-summary: Manage file copy operations.
"""

helps['storage file metadata'] = """
    type: group
    short-summary: Manage file metadata.
"""

helps['storage logging'] = """
    type: group
    short-summary: Manage Storage service logging information.
"""

helps['storage message'] = """
    type: group
    short-summary: Manage queue storage messages.
"""

helps['storage metrics'] = """
    type: group
    short-summary: Manage Storage service metrics.
"""

helps['storage queue'] = """
    type: group
    short-summary: Effectively scale apps according to traffic using queues.
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

helps['storage table policy'] = """
    type: group
    short-summary: Manage storage table shared access policies.
"""
