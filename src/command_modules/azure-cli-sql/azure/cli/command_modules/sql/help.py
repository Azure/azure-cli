# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long

helps['sql'] = """
            type: group
            short-summary: Manage Azure SQL databases.
            """
helps['sql server'] = """
            type: group
            short-summary: Manage servers.
            """
helps['sql server create'] = """
            type: command
            short-summary: Create an Azure SQL server.
            """
helps['sql server list'] = """
            type: command
            short-summary: List Azure SQL servers.
            """
helps['sql server update'] = """
            type: command
            short-summary: Update a Azure SQL server.
            """
helps['sql server firewall'] = """
            type: group
            short-summary: Manage Azure SQL server's firewall rules.
            """
helps['sql server firewall create'] = """
            type: command
            short-summary: Create an Azure SQL server firewall rule.
            """
helps['sql server firewall update'] = """
            type: command
            short-summary: Update an Azure SQL server firewall rule.
            """
helps['sql server firewall show'] = """
            type: command
            short-summary: Show the details of an Azure SQL server firewall rule.
            """
helps['sql server firewall list'] = """
            type: command
            short-summary: List the Azure SQL server firewall rules.
            """
helps['sql server service-objective'] = """
            type: group
            short-summary: Show Azure SQL server's service objectives.
            """
helps['sql db'] = """
            type: group
            short-summary: Manage databases.
            """
helps['sql db create'] = """
            type: command
            short-summary: Create an Azure SQL database.
            """
helps['sql db replication-link'] = """
            type: group
            short-summary: Manage database replication links.
            """
helps['sql db data-warehouse'] = """
            type: group
            short-summary: Manage database data warehouse.
            """
helps['sql db restore-point'] = """
            type: group
            short-summary: Manage database restore points.
            """
helps['sql db transparent-data-encryption'] = """
            type: group
            short-summary: Manage database transparent data encryption.
            """
helps['sql db service-tier-advisor'] = """
            type: group
            short-summary: Manage database service tier advisors.
            """
helps['sql elastic-pools'] = """
            type: group
            short-summary: Manage database elastic pools.
            """
helps['sql elastic-pools update'] = """
            type: command
            short-summary: Update a database elastic pool.
            """
helps['sql elastic-pools db'] = """
            type: group
            short-summary: Manage databases activities in database elastic pools.
            """
helps['sql elastic-pools recommended'] = """
            type: group
            short-summary: Get information about an Azure SQL recommended elastic pool.
            """
helps['sql elastic-pools recommended db'] = """
            type: group
            short-summary: Get information about an Azure SQL database inside of recommended elastic pool.
            """
