# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


helps['cosmosdb'] = """
    type: group
    short-summary: Manage Azure Cosmos DB database accounts.
"""

helps['cosmosdb database'] = """
    type: group
    short-summary: Manage Azure Cosmos DB databases.
"""

helps['cosmosdb collection'] = """
    type: group
    short-summary: Manage Azure Cosmos DB collections.
"""

helps['cosmosdb check-name-exists'] = """
    type: command
    short-summary: Checks that the Azure Cosmos DB account name already exists.
"""

helps['cosmosdb create'] = """
    type: command
    short-summary: Create a new Azure Cosmos DB database account.
"""

helps['cosmosdb delete'] = """
    type: command
    short-summary: Deletes an existing Azure Cosmos DB database account.
"""

helps['cosmosdb failover-priority-change'] = """
    type: command
    short-summary: Changes the failover priority for the Azure Cosmos DB database account.
"""

helps['cosmosdb list'] = """
    type: command
    short-summary: Lists all Azure Cosmos DB database accounts within a given resource group or subscription.
"""

helps['cosmosdb list-connection-strings'] = """
    type: command
    short-summary: Lists the connection strings for the specified Azure Cosmos DB database account.
"""

helps['cosmosdb list-keys'] = """
    type: command
    short-summary: Lists the access keys for the specified Azure Cosmos DB database account.
"""

helps['cosmosdb list-read-only-keys'] = """
    type: command
    short-summary: Lists the read-only access keys for the specified Azure Cosmos DB database account.
"""

helps['cosmosdb regenerate-key'] = """
    type: command
    short-summary: Regenerates an access key for the specified Azure Cosmos DB database account.
"""

helps['cosmosdb show'] = """
    type: command
    short-summary: Retrieves the properties of an existing Azure Cosmos DB database account.
"""

helps['cosmosdb update'] = """
    type: command
    short-summary: Update an existing Azure Cosmos DB database account.
"""
