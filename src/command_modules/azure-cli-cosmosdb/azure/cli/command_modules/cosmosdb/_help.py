# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps  # pylint: disable=unused-import


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
    type: commanad
    short-summary: Checks that the Azure Cosmos DB account name already exists.
"""

helps['cosmosdb create'] = """
    type: commanad
    short-summary: Create a new Azure Cosmos DB database account.
"""

helps['cosmosdb delete'] = """
    type: commanad
    short-summary: Deletes an existing Azure Cosmos DB database account.
"""

helps['cosmosdb failover-priority-change'] = """
    type: commanad
    short-summary: Changes the failover priority for the Azure Cosmos DB database account.
"""

helps['cosmosdb list'] = """
    type: commanad
    short-summary: Lists all Azure Cosmos DB database accounts within a given resource group or subscription.
"""

helps['cosmosdb list-connection-strings'] = """
    type: commanad
    short-summary: Lists the connection strings for the specified Azure Cosmos DB database account.
"""

helps['cosmosdb list-keys'] = """
    type: commanad
    short-summary: Lists the access keys for the specified Azure Cosmos DB database account.
"""

helps['cosmosdb list-read-only-keys'] = """
    type: commanad
    short-summary: Lists the read-only access keys for the specified Azure Cosmos DB database account.
"""

helps['cosmosdb regenerate-key'] = """
    type: commanad
    short-summary: Regenerates an access key for the specified Azure Cosmos DB database account.
"""

helps['cosmosdb show'] = """
    type: commanad
    short-summary: Retrieves the properties of an existing Azure Cosmos DB database account.
"""

helps['cosmosdb update'] = """
    type: commanad
    short-summary: Update an existing Azure Cosmos DB database account.
"""
