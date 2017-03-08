# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long
helps['datalake'] = """
    type: group
    short-summary: Access to Data Lake Analytics and Store management
    long-summary: If you don't have the datalake component installed, add it with `az component update --add datalake`
"""

helps['datalake store'] = """
    type: group
    short-summary: Commands to manage Data Lake Store accounts, and filesystems. 
"""

helps['datalake store account'] = """
    type: group
    short-summary: Commands to manage Data Lake Store accounts. 
"""

helps['datalake store account create'] = """
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

helps['datalake store account update'] = """
    type: command
    short-summary: Updates a Data Lake Store account. 
"""

helps['datalake store account show'] = """
    type: command
    short-summary: Retrieves the Data Lake Store account. 
"""

helps['datalake store account list'] = """
    type: command
    short-summary: Lists Data Lake Store accounts in a subscription or a specific resource group. 
"""

helps['datalake store account delete'] = """
    type: command
    short-summary: Deletes the Data Lake Store account. 
"""

helps['datalake store account trusted-provider'] = """
    type: group
    short-summary: Commands to manage Data Lake Store account trusted identity providers. 
"""

helps['datalake store account firewall'] = """
    type: group
    short-summary: Commands to manage Data Lake Store account firewall rules. 
"""

helps['datalake store account firewall create'] = """
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

helps['datalake store account firewall update'] = """
    type: command
    short-summary: Updates a firewall rule in the Data Lake Store account. 
"""

helps['datalake store account firewall show'] = """
    type: command
    short-summary: Retrieves a firewall rule in the Data Lake Store account. 
"""

helps['datalake store account firewall list'] = """
    type: command
    short-summary: Lists firewall rules in the Data Lake Store account. 
"""

helps['datalake store account firewall delete'] = """
    type: command
    short-summary: Deletes a firewall rule in the Data Lake Store account. 
"""

helps['datalake store file'] = """
    type: group
    short-summary: Commands to manage a Data Lake Store filesystem. 
"""

helps['datalake store file create'] = """
    type: command
    short-summary: Creates a file or folder in the Data Lake Store account at the path.
    parameters:
        - name: --content
          type: string
          short-summary: 'Optional content for the file to contain upon creation.'
"""

helps['datalake store file show'] = """
    type: command
    short-summary: displays file or folder information in the Data Lake Store account at the path.
"""

helps['datalake store file list'] = """
    type: command
    short-summary: displays the list of files and folder information under the folder in the Data Lake Store account.
"""

helps['datalake store file append'] = """
    type: command
    short-summary: Appends content to a file in the Data Lake Store account at the path.
    parameters:
        - name: --content
          type: string
          short-summary: 'Content to be appended to the file.'
"""

helps['datalake store file delete'] = """
    type: command
    short-summary: Deletes the file or folder in the Data Lake Store account at the path.
"""

helps['datalake store file upload'] = """
    type: command
    short-summary: Uploads a file or folder to the Data Lake Store account at the destination path.
    parameters:
        - name: --source-path
          type: string
          short-summary: 'The full path to the file or folder to upload'
        - name: --destination-path
          type: string
          short-summary: 'The full path in the Data Lake store filesystem to upload the file or folder to in the format /path/file.txt'
        - name: --thread-count
          type: int
          short-summary: 'Optionally specify the parallelism of the upload. Default is the number of cores in the local machine.'
"""

helps['datalake store file download'] = """
    type: command
    short-summary: Downloads a file or folder from the Data Lake Store account to the local destination path.
    parameters:
        - name: --source-path
          type: string
          short-summary: 'The full path in the Data Lake store filesystem to download the file or folder from in the format /path/file.txt'
        - name: --destination-path
          type: string
          short-summary: 'The full local path where the file or folder will be downloaded to'
        - name: --thread-count
          type: int
          short-summary: 'Optionally specify the parallelism of the download. Default is the number of cores in the local machine.'
"""

helps['datalake store file test'] = """
    type: command
    short-summary: Tests the existence of the file or folder in the Data Lake Store account at the path.
"""

helps['datalake store file preview'] = """
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

helps['datalake store file join'] = """
    type: command
    short-summary: Joins the list of files in the Data Lake Store account into one file at the destination path.
    parameters:
        - name: --source-paths
          type: list
          short-summary: 'The list of files in the Data Lake Store account to join.'
        - name: --destination-path
          type: string
          short-summary: 'The destination path in the Data Lake store account where the resulting joined files should be placed.'
"""

helps['datalake store file move'] = """
    type: command
    short-summary: Moves the file or folder in the Data Lake Store account to the destination path.
    parameters:
        - name: --source-path
          type: list
          short-summary: 'The file or folder to move'
        - name: --destination-path
          type: string
          short-summary: 'The destination path in the Data Lake store account where the file or folder should be moved to.'
"""

helps['datalake store file set-owner'] = """
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

helps['datalake store file set-permission'] = """
    type: command
    short-summary: Sets the permission octal for the file or folder in the Data Lake Store account.
    parameters:
        - name: --permission
          type: int
          short-summary: 'The octal representation of the permissions for user, group and mask (for example: 777 is full rwx for all entities)'
"""