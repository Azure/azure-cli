#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps #pylint: disable=unused-import

#pylint: disable=line-too-long

helps['keyvault'] = """
    type: group
    short-summary: Safeguard and maintain control of keys, secrets, and certificates.
"""

helps['keyvault create'] = """
    type: command
    short-summary: Create a new Key Vault.
    long-summary: "Default permissions are created for the current user unless the --no-self-perms
        flag is specified."
"""

helps['keyvault delete'] = """
    type: command
    short-summary: Delete a Key Vault.
"""

helps['keyvault list'] = """
    type: command
    short-summary: List Key Vaults within a subscription or resource group.
"""

helps['keyvault show'] = """
    type: command
    short-summary: Show details of a Key Vault.
"""

helps['keyvault update'] = """
    type: command
    short-summary: Update properties of a Key Vault.
"""
