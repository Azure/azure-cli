#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

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
    short-summary: Commands to manage your Storage accounts
"""
helps['storage account keys'] = """
    type: group
    short-summary: Commands to manage your Storage account keys
"""
helps['storage blob'] = """
    type: group
    short-summary: Object storage for unstructured data
"""
helps['storage blob copy'] = """
    type: group
    short-summary: Commands to manage your blob copy operations
"""
helps['storage blob lease'] = """
    type: group
    short-summary: Commands to manage leases of your storage blob
"""
helps['storage blob metadata'] = """
    type: group
    short-summary: Commands to manage your blob metadata
"""
helps['storage blob service-properties'] = """
    type: group
    short-summary: Commands to view Storage blob service properties
"""
helps['storage container'] = """
    type: group
    short-summary: Commands to manage your storage containers
"""
helps['storage container lease'] = """
    type: group
    short-summary: Commands to manage leases of your storage containers
"""
helps['storage container metadata'] = """
    type: group
    short-summary: Commands to manage your storage container metadata
"""
helps['storage container policy'] = """
    type: group
    short-summary: Commands to manage stored access policies of your storage container
"""
helps['storage cors'] = """
    type: group
    short-summary: Commands to manage your Storage Cross-Orgin Resource Sharing (CORS)
"""
helps['storage directory'] = """
    type: group
    short-summary: Commands to manage your Storage file directory
"""
helps['storage directory metadata'] = """
    type: group
    short-summary: Commands to manage your Storage file directory metadata
"""
helps['storage entity'] = """
    type: group
    short-summary: Commands to manage Storage table entities
"""
helps['storage file'] = """
    type: group
    short-summary: File shares that use the standard SMB 3.0 protocal
"""
helps['storage file copy'] = """
    type: group
    short-summary: Commands to manage your file copy operations
"""
helps['storage file metadata'] = """
    type: group
    short-summary: Commands to manage your file metadata
"""
helps['storage logging'] = """
    type: group
    short-summary: Commands to view Storage logging information
"""
helps['storage message'] = """
    type: group
    short-summary: Commands to manage Storage queue messages
"""
helps['storage metrics'] = """
    type: group
    short-summary: Commands to manage your Storage metrics properties
"""
helps['storage queue'] = """
    type: group
    short-summary: Effectively scale apps according to traffic using queues
"""
helps['storage queue metadata'] = """
    type: group
    short-summary: Commands to manage your queue metadata
"""
helps['storage queue policy'] = """
    type: group
    short-summary: Commands to manage shared access policies of your storage queue
"""
helps['storage share'] = """
    type: group
    short-summary: Commands to manage Storage file shares
"""
helps['storage share metadata'] = """
    type: group
    short-summary: Commands to manage file share metadata
"""
helps['storage share policy'] = """
    type: group
    short-summary: Commands to manage stored access policies of your Storage file share
"""
helps['storage table'] = """
    type: group
    short-summary: NoSQL key-value storage using semi-structured datasets
"""
helps['storage table policy'] = """
    type: group
    short-summary: Commands to manage stored access policies of your Storage table
"""
