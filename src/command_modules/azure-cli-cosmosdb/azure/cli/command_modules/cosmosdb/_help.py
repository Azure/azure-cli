# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

helps["cosmosdb"] = """
type: group
short-summary: Manage Azure Cosmos DB database accounts.
"""

helps["cosmosdb check-name-exists"] = """
type: command
short-summary: Checks if an Azure Cosmos DB account name exists.
examples:
-   name: Checks if an Azure Cosmos DB account name exists.
    text: az cosmosdb check-name-exists --name MyCosmosDBDatabaseAccount
    crafted: 'True'
"""

helps["cosmosdb collection"] = """
type: group
short-summary: Manage Azure Cosmos DB collections.
"""

helps["cosmosdb create"] = """
type: command
short-summary: Creates a new Azure Cosmos DB database account.
examples:
-   name: Creates a new Azure Cosmos DB database account.
    text: az cosmosdb create --resource-group MyResourceGroup --name MyCosmosDBDatabaseAccount
    crafted: 'True'
"""

helps["cosmosdb database"] = """
type: group
short-summary: Manage Azure Cosmos DB databases.
"""

helps["cosmosdb delete"] = """
type: command
short-summary: Deletes an Azure Cosmos DB database account.
examples:
-   name: Deletes an Azure Cosmos DB database account.
    text: az cosmosdb delete --resource-group MyResourceGroup --name MyCosmosDBDatabaseAccount
    crafted: 'True'
"""

helps["cosmosdb failover-priority-change"] = """
type: command
short-summary: Changes the failover priority for the Azure Cosmos DB database account.
"""

helps["cosmosdb list"] = """
type: command
short-summary: List Azure Cosmos DB database accounts.
"""

helps["cosmosdb list-connection-strings"] = """
type: command
short-summary: List the connection strings for a Azure Cosmos DB database account.
examples:
-   name: List the connection strings for a Azure Cosmos DB database account.
    text: az cosmosdb list-connection-strings --resource-group MyResourceGroup --name
        MyCosmosDBDatabaseAccount
    crafted: 'True'
"""

helps["cosmosdb list-keys"] = """
type: command
short-summary: List the access keys for a Azure Cosmos DB database account.
examples:
-   name: List the access keys for a Azure Cosmos DB database account.
    text: az cosmosdb list-keys --resource-group MyResourceGroup --name MyCosmosDBDatabaseAccount
    crafted: 'True'
"""

helps["cosmosdb list-read-only-keys"] = """
type: command
short-summary: List the read-only access keys for a Azure Cosmos DB database account.
"""

helps["cosmosdb regenerate-key"] = """
type: command
short-summary: Regenerate an access key for a Azure Cosmos DB database account.
"""

helps["cosmosdb show"] = """
type: command
short-summary: Get the details of an Azure Cosmos DB database account.
examples:
-   name: Get the details of an Azure Cosmos DB database account.
    text: az cosmosdb show --resource-group MyResourceGroup --name MyCosmosDBDatabaseAccount
    crafted: 'True'
"""

helps["cosmosdb update"] = """
type: command
short-summary: Update an Azure Cosmos DB database account.
"""

