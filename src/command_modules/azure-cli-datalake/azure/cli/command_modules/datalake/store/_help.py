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
    short-summary: Retrieves the specified Data Lake Store account. 
"""

helps['datalake store account list'] = """
    type: command
    short-summary: Lists Data Lake Store accounts in a subscription or a specific resource group. 
"""

helps['datalake store account delete'] = """
    type: command
    short-summary: Deletes the specified Data Lake Store account. 
"""

helps['datalake store account firewall'] = """
    type: group
    short-summary: Commands to manage Data Lake Store account firewall rules. 
"""

helps['datalake store account firewall create'] = """
    type: command
    short-summary: Creates a firewall rule in the specified Data Lake Store account.
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
    short-summary: Updates a firewall rule in the specified Data Lake Store account. 
"""

helps['datalake store account firewall show'] = """
    type: command
    short-summary: Retrieves a firewall rule in the specified Data Lake Store account. 
"""

helps['datalake store account firewall list'] = """
    type: command
    short-summary: Lists firewall rules in the specified Data Lake Store account. 
"""

helps['datalake store account firewall delete'] = """
    type: command
    short-summary: Deletes a firewall rule in the specified Data Lake Store account. 
"""

helps['datalake store account provider'] = """
    type: group
    short-summary: Commands to manage Data Lake Store account trusted identity providers. 
"""

helps['datalake store account provider add'] = """
    type: command
    short-summary: Adds a trusted identity provider to the specified Data Lake Store account. 
"""

helps['datalake store account provider update'] = """
    type: command
    short-summary: Updates a trusted identity provider in the specified Data Lake Store account. 
"""

helps['datalake store account provider show'] = """
    type: command
    short-summary: Retrieves a trusted identity provider in the specified Data Lake Store account. 
"""

helps['datalake store account provider list'] = """
    type: command
    short-summary: Lists trusted identity providers in the specified Data Lake Store account. 
"""

helps['datalake store account provider delete'] = """
    type: command
    short-summary: Deletes a trusted identity provider in the specified Data Lake Store account. 
"""