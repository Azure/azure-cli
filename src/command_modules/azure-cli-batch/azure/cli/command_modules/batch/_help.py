# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

#pylint: disable=line-too-long

helps['batch'] = """
    type: group
    short-summary: Commands for working with Azure Batch.
"""

helps['batch account'] = """
    type: group
    short-summary: Commands to manage your Batch accounts.
"""

helps['batch account list'] = """
    type: command
    short-summary: Lists the Batch accounts associated with a subscription or resource group.
"""

helps['batch account create'] = """
    type: command
    short-summary: Creates a new Batch account with the specified parameters.
"""

helps['batch account autostorage-keys'] = """
    type: group
    short-summary: Commands to manage the access keys for the auto storage account configured for your Batch account.
"""

helps['batch account keys'] = """
    type: group
    short-summary: Commands to manage your Batch account keys.
"""

helps['batch application'] = """
    type: group
    short-summary: Commands to manage your Batch applications.
"""

helps['batch application package'] = """
    type: group
    short-summary: Commands to manage your Batch application packages.
"""

helps['batch location'] = """
    type: group
    short-summary: Commands to manage Batch service options for a subscription at the region level.
"""

helps['batch location quotas'] = """
    type: group
    short-summary: Commands to manage Batch service quotas at the region level.
"""
