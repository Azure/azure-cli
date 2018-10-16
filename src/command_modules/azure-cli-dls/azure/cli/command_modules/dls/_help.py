# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


helps['dls'] = """
    type: group
    short-summary: (PREVIEW) Manage Data Lake Store accounts and filesystems.
"""

helps['dls account'] = """
    type: group
    short-summary: (PREVIEW) Manage Data Lake Store accounts.
"""

helps['dls account create'] = """
    type: command
    short-summary: Creates a Data Lake Store account.
    parameters:
        - name: --default-group
          type: string
          short-summary: 'Name of the default group to give permissions to for freshly created files and folders in the Data Lake Store account.'
        - name: --key-vault-id
          type: string
          short-summary: 'Key vault for the user-assigned encryption type.'
        - name: --key-name
          type: string
          short-summary: 'Key name for the user-assigned encryption type.'
        - name: --key-version
          type: string
          short-summary: 'Key version for the user-assigned encryption type.'
"""

helps['dls account update'] = """
    type: command
    short-summary: Updates a Data Lake Store account.
"""

helps['dls account show'] = """
    type: command
    short-summary: Get the details of a Data Lake Store account.
"""

helps['dls account list'] = """
    type: command
    short-summary: Lists available Data Lake Store accounts.
"""

helps['dls account enable-key-vault'] = """
    type: command
    short-summary: Enable the use of Azure Key Vault for encryption of a Data Lake Store account.
"""

helps['dls account delete'] = """
    type: command
    short-summary: Delete a Data Lake Store account.
"""

helps['dls account trusted-provider'] = """
    type: group
    short-summary: (PREVIEW) Manage Data Lake Store account trusted identity providers.
"""

helps['dls account firewall'] = """
    type: group
    short-summary: (PREVIEW) Manage Data Lake Store account firewall rules.
"""

helps['dls account firewall create'] = """
    type: command
    short-summary: Creates a firewall rule in a Data Lake Store account.
    parameters:
        - name: --end-ip-address
          type: string
          short-summary: 'The end of the valid ip range for the firewall rule.'
        - name: --start-ip-address
          type: string
          short-summary: 'The start of the valid ip range for the firewall rule.'
        - name: --firewall-rule-name
          type: string
          short-summary: 'The name of the firewall rule.'
"""

helps['dls account firewall update'] = """
    type: command
    short-summary: Updates a firewall rule in a Data Lake Store account.
"""

helps['dls account firewall show'] = """
    type: command
    short-summary: Get the details of a firewall rule in a Data Lake Store account.
"""

helps['dls account firewall list'] = """
    type: command
    short-summary: Lists firewall rules in a Data Lake Store account.
"""

helps['dls account firewall delete'] = """
    type: command
    short-summary: Deletes a firewall rule in a Data Lake Store account.
"""

helps['dls account network-rule'] = """
    type: group
    short-summary: (PREVIEW) Manage Data Lake Store account virtual network rules.
"""

helps['dls account network-rule create'] = """
    type: command
    short-summary: Creates a virtual network rule in a Data Lake Store account.
    parameters:
        - name: --subnet
          type: string
          short-summary: 'The subnet name or id for the virtual network rule.'
        - name: --vnet-name
          type: string
          short-summary: 'The name of the virtual network rule.'
"""

helps['dls account network-rule update'] = """
    type: command
    short-summary: Updates a virtual network rule in a Data Lake Store account.
"""

helps['dls account network-rule show'] = """
    type: command
    short-summary: Get the details of a virtual network rule in a Data Lake Store account.
"""

helps['dls account network-rule list'] = """
    type: command
    short-summary: Lists virtual network rules in a Data Lake Store account.
"""

helps['dls account network-rule delete'] = """
    type: command
    short-summary: Deletes a virtual network rule in a Data Lake Store account.
"""

helps['dls fs'] = """
    type: group
    short-summary: (PREVIEW) Manage a Data Lake Store filesystem.
"""

helps['dls fs create'] = """
    type: command
    short-summary: Creates a file or folder in a Data Lake Store account.
    parameters:
        - name: --content
          type: string
          short-summary: 'Content for the file to contain upon creation.'
"""

helps['dls fs show'] = """
    type: command
    short-summary: Get file or folder information in a Data Lake Store account.
"""

helps['dls fs list'] = """
    type: command
    short-summary: List the files and folders in a Data Lake Store account.
"""

helps['dls fs append'] = """
    type: command
    short-summary: Append content to a file in a Data Lake Store account.
    parameters:
        - name: --content
          type: string
          short-summary: 'Content to be appended to the file.'
"""

helps['dls fs delete'] = """
    type: command
    short-summary: Delete a file or folder in a Data Lake Store account.
"""

helps['dls fs upload'] = """
    type: command
    short-summary: Upload a file or folder to a Data Lake Store account.
    parameters:
        - name: --source-path
          type: string
          short-summary: The path to the file or folder to upload.
        - name: --destination-path
          type: string
          short-summary: The full path in the Data Lake Store filesystem to upload the file or folder to.
        - name: --thread-count
          type: int
          short-summary: 'Parallelism of the upload. Default: The number of cores in the local machine.'
        - name: --chunk-size
          type: int
          short-summary: Size of a chunk, in bytes.
          long-summary: Large files are split into chunks. Files smaller than this size will always be transferred in a single thread.
        - name: --buffer-size
          type: int
          short-summary: Size of the transfer buffer, in bytes.
          long-summary: A buffer cannot be bigger than a chunk and cannot be smaller than a block.
        - name: --block-size
          type: int
          short-summary: Size of a block, in bytes.
          long-summary: Within each chunk, a smaller block is written for each API call. A block cannot be bigger than a chunk and must be bigger than a buffer.

"""

helps['dls fs download'] = """
    type: command
    short-summary: Download a file or folder from a Data Lake Store account to the local machine.
    parameters:
        - name: --source-path
          type: string
          short-summary: The full path in the Data Lake Store filesystem to download the file or folder from.
        - name: --destination-path
          type: string
          short-summary: The local path where the file or folder will be downloaded to.
        - name: --thread-count
          type: int
          short-summary: 'Parallelism of the download. Default: The number of cores in the local machine.'
        - name: --chunk-size
          type: int
          short-summary: Size of a chunk, in bytes.
          long-summary: Large files are split into chunks. Files smaller than this size will always be transferred in a single thread.
        - name: --buffer-size
          type: int
          short-summary: Size of the transfer buffer, in bytes.
          long-summary: A buffer cannot be bigger than a chunk and cannot be smaller than a block.
        - name: --block-size
          type: int
          short-summary: Size of a block, in bytes.
          long-summary: Within each chunk, a smaller block is written for each API call. A block cannot be bigger than a chunk and must be bigger than a buffer.
"""

helps['dls fs test'] = """
    type: command
    short-summary: Test for the existence of a file or folder in a Data Lake Store account.
"""

helps['dls fs preview'] = """
    type: command
    short-summary: Preview the content of a file in a Data Lake Store account.
    parameters:
        - name: --length
          type: long
          short-summary: The amount of data to preview in bytes.
          long-summary: If not specified, attempts to preview the full file. If the file is > 1MB `--force` must be specified.
        - name: --offset
          type: long
          short-summary: The position in bytes to start the preview from.
"""

helps['dls fs join'] = """
    type: command
    short-summary: Join files in a Data Lake Store account into one file.
    parameters:
        - name: --source-paths
          type: list
          short-summary: The space-separated list of files in the Data Lake Store account to join.
        - name: --destination-path
          type: string
          short-summary: The destination path in the Data Lake Store account.
"""

helps['dls fs move'] = """
    type: command
    short-summary: Move a file or folder in a Data Lake Store account.
    parameters:
        - name: --source-path
          type: list
          short-summary: The file or folder to move.
        - name: --destination-path
          type: string
          short-summary: The destination path in the Data Lake Store account.
"""

helps['dls fs set-expiry'] = """
    type: command
    short-summary: Set the expiration time for a file.
"""

helps['dls fs remove-expiry'] = """
    type: command
    short-summary: Remove the expiration time for a file.
"""

helps['dls fs access'] = """
    type: group
    short-summary: Manage Data Lake Store filesystem access and permissions.
"""

helps['dls fs access show'] = """
    type: command
    short-summary: Display the access control list (ACL).
"""

helps['dls fs access set-owner'] = """
    type: command
    short-summary: Set the owner information for a file or folder in a Data Lake Store account.
    parameters:
        - name: --owner
          type: string
          short-summary: The user Azure Active Directory object ID or user principal name to set as the owner.
        - name: --group
          type: string
          short-summary: The group Azure Active Directory object ID or user principal name to set as the owning group.
"""

helps['dls fs access set-permission'] = """
    type: command
    short-summary: Set the permissions for a file or folder in a Data Lake Store account.
    parameters:
        - name: --permission
          type: int
          short-summary: The octal representation of the permissions for user, group and mask.
    example:
        - name: Set full permissions for a user, read-execute permissions for a group, and execute permissions for all.
          text: az fs access set-permission --path /path/to/file.txt --permission 751
"""

helps['dls fs access set-entry'] = """
    type: command
    short-summary: Update the access control list for a file or folder.
"""

helps['dls fs access set'] = """
    type: command
    short-summary: Replace the existing access control list for a file or folder.
"""

helps['dls fs access remove-entry'] = """
    type: command
    short-summary: Remove entries for the access control list of a file or folder.
"""

helps['dls fs access remove-all'] = """
    type: command
    short-summary: Remove the access control list for a file or folder.
"""
