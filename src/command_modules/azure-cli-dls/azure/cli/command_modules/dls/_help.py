# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['dls'] = """
    type: group
    short-summary: Commands to manage Data Lake Store accounts, and filesystems.
    long-summary: If you don't have the Data Lake Store component installed, add it with `az component update --add dls`. These commands are in preview.
"""

helps['dls account'] = """
    type: group
    short-summary: Commands to manage Data Lake Store accounts.
    long-summary: These commands are in preview.
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
          short-summary: 'If the encryption type is User assigned, this is the key vault the user wishes to use.'
        - name: --key-name
          type: string
          short-summary: 'If the encryption type is User assigned, this is the key name in the key vault the user wishes to use.'
        - name: --key-version
          type: string
          short-summary: 'If the encryption type is User assigned, this is the key version of the key the user wishes to use.'
"""

helps['dls account update'] = """
    type: command
    short-summary: Updates a Data Lake Store account.
"""

helps['dls account show'] = """
    type: command
    short-summary: Retrieves the Data Lake Store account.
"""

helps['dls account list'] = """
    type: command
    short-summary: Lists Data Lake Store accounts in a subscription or a specific resource group.
"""

helps['dls account enable-key-vault'] = """
    type: command
    short-summary: Attempts to enable a user managed Key Vault for encryption of the specified Data Lake Store account.
"""

helps['dls account delete'] = """
    type: command
    short-summary: Deletes the Data Lake Store account.
"""

helps['dls account trusted-provider'] = """
    type: group
    short-summary: Commands to manage Data Lake Store account trusted identity providers.
    long-summary: These commands are in preview.
"""

helps['dls account firewall'] = """
    type: group
    short-summary: Commands to manage Data Lake Store account firewall rules.
    long-summary: These commands are in preview.
"""

helps['dls account firewall create'] = """
    type: command
    short-summary: Creates a firewall rule in the Data Lake Store account.
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
    short-summary: Updates a firewall rule in the Data Lake Store account.
"""

helps['dls account firewall show'] = """
    type: command
    short-summary: Retrieves a firewall rule in the Data Lake Store account.
"""

helps['dls account firewall list'] = """
    type: command
    short-summary: Lists firewall rules in the Data Lake Store account.
"""

helps['dls account firewall delete'] = """
    type: command
    short-summary: Deletes a firewall rule in the Data Lake Store account.
"""

helps['dls fs'] = """
    type: group
    short-summary: Commands to manage a Data Lake Store filesystem.
    long-summary: These commands are in preview.
"""

helps['dls fs create'] = """
    type: command
    short-summary: Creates a file or folder in the Data Lake Store account at the path.
    parameters:
        - name: --content
          type: string
          short-summary: 'Optional content for the file to contain upon creation.'
"""

helps['dls fs show'] = """
    type: command
    short-summary: displays file or folder information in the Data Lake Store account at the path.
"""

helps['dls fs list'] = """
    type: command
    short-summary: displays the list of files and folder information under the folder in the Data Lake Store account.
"""

helps['dls fs append'] = """
    type: command
    short-summary: Appends content to a file in the Data Lake Store account at the path.
    parameters:
        - name: --content
          type: string
          short-summary: 'Content to be appended to the file.'
"""

helps['dls fs delete'] = """
    type: command
    short-summary: Deletes the file or folder in the Data Lake Store account at the path.
"""

helps['dls fs upload'] = """
    type: command
    short-summary: Uploads a file or folder to the Data Lake Store account at the destination path.
    parameters:
        - name: --source-path
          type: string
          short-summary: 'The full path to the file or folder to upload'
        - name: --destination-path
          type: string
          short-summary: 'The full path in the Data Lake Store filesystem to upload the file or folder to in the format /path/file.txt'
        - name: --thread-count
          type: int
          short-summary: 'Optionally specify the parallelism of the upload. Default is the number of cores in the local machine.'
"""

helps['dls fs download'] = """
    type: command
    short-summary: Downloads a file or folder from the Data Lake Store account to the local destination path.
    parameters:
        - name: --source-path
          type: string
          short-summary: 'The full path in the Data Lake Store filesystem to download the file or folder from in the format /path/file.txt'
        - name: --destination-path
          type: string
          short-summary: 'The full local path where the file or folder will be downloaded to'
        - name: --thread-count
          type: int
          short-summary: 'Optionally specify the parallelism of the download. Default is the number of cores in the local machine.'
"""

helps['dls fs test'] = """
    type: command
    short-summary: Tests the existence of the file or folder in the Data Lake Store account at the path.
"""

helps['dls fs preview'] = """
    type: command
    short-summary: Previews the content of the file in the Data Lake Store account at the path.
    parameters:
        - name: --length
          type: long
          short-summary: 'The optional amount of data to preview in bytes as a long. If not specified, will attempt to preview the full file. If the file is > 1MB --force must be specified'
        - name: --offset
          type: long
          short-summary: 'The optional position in bytes as a long in the file to start the preview from'
"""

helps['dls fs join'] = """
    type: command
    short-summary: Joins the list of files in the Data Lake Store account into one file at the destination path.
    parameters:
        - name: --source-paths
          type: list
          short-summary: 'The list of files in the Data Lake Store account to join.'
        - name: --destination-path
          type: string
          short-summary: 'The destination path in the Data Lake Store account where the resulting joined files should be placed.'
"""

helps['dls fs move'] = """
    type: command
    short-summary: Moves the file or folder in the Data Lake Store account to the destination path.
    parameters:
        - name: --source-path
          type: list
          short-summary: 'The file or folder to move'
        - name: --destination-path
          type: string
          short-summary: 'The destination path in the Data Lake Store account where the file or folder should be moved to.'
"""

helps['dls fs set-expiry'] = """
    type: command
    short-summary: Sets the absolute expiration time of the file.
"""

helps['dls fs remove-expiry'] = """
    type: command
    short-summary: Removes the expiration time on a file, if any.
"""

helps['dls fs access'] = """
    type: group
    short-summary: Commands to manage a Data Lake Store filesystem access and permissions.
"""

helps['dls fs access show'] = """
    type: command
    short-summary: Displays the ACL for a given file or folder
"""

helps['dls fs access set-owner'] = """
    type: command
    short-summary: Sets the owner and or owning group for the file or folder in the Data Lake Store account.
    parameters:
        - name: --owner
          type: string
          short-summary: 'The user AAD object ID or UPN to set as the owner. If not specified the owner remains unchanged'
        - name: --group
          type: string
          short-summary: 'The group AAD object ID or UPN to set as the owning group. If not specified the owning group remains unchanged'
"""

helps['dls fs access set-permission'] = """
    type: command
    short-summary: Sets the permission octal for the file or folder in the Data Lake Store account.
    parameters:
        - name: --permission
          type: int
          short-summary: 'The octal representation of the permissions for user, group and mask (for example: 777 is full rwx for all entities)'
"""

helps['dls fs access set-entry'] = """
    type: command
    short-summary: updates the existing ACL on the file or folder to include or update the entries specified
"""

helps['dls fs access set'] = """
    type: command
    short-summary: replaces the existing ACL on the file or folder with the specified ACL, which must contain all unnamed entries
"""

helps['dls fs access remove-entry'] = """
    type: command
    short-summary: updates the existing ACL on the file or folder to remove the entries specified if they exist
"""

helps['dls fs access remove-all'] = """
    type: command
    short-summary: completely removes the existing ACL or default ACL on the file or folder
"""
