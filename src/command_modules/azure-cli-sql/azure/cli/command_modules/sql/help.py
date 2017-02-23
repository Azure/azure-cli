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
helps['sql db'] = """
            type: group
            short-summary: Manage databases.
            """
helps['sql db copy'] = """
            type: command
            short-summary: Creates a copy of an existing Azure SQL Database.
            """
helps['sql db create'] = """
            type: command
            short-summary: Creates an Azure SQL Database.
            """
helps['sql db create-secondary'] = """
            type: command
            short-summary: Creates a readable secondary replica of an existing Azure SQL Database.
            """
helps['sql db list'] = """
            type: command
            short-summary: Lists all Azure SQL Databases in a server.
            """
helps['sql db update'] = """
            type: command
            short-summary: Updates an Azure SQL Database.
            """
helps['sql db replication-link'] = """
            type: group
            short-summary: Manage database replication links.
            """
#helps['sql db data-warehouse'] = """
#            type: group
#            short-summary: Manage database data warehouse.
#            """
#helps['sql db restore-point'] = """
#            type: group
#            short-summary: Manage database restore points.
#            """
#helps['sql db transparent-data-encryption'] = """
#            type: group
#            short-summary: Manage database transparent data encryption.
#            """
#helps['sql db service-tier-advisor'] = """
#            type: group
#            short-summary: Manage database service tier advisors.
#            """
helps['sql elastic-pool'] = """
            type: group
            short-summary: Manage elastic pools. An elastic pool is an allocation of CPU, IO, and memory resources. Databases inside the pool share these resources.
            """
helps['sql elastic-pool create'] = """
            type: command
            short-summary: Creates an elastic pool.
            """
helps['sql elastic-pool update'] = """
            type: command
            short-summary: Updates an elastic pool.
            """
#helps['sql elastic-pool db'] = """
#            type: group
#            short-summary: Command to manage databases activities in database elastic pools.
#            """
#helps['sql elastic-pool recommended'] = """
#            type: group
#            short-summary: Get information about an Azure SQL Recommended Elastic Pool.
#            """
#helps['sql elastic-pool recommended db'] = """
#            type: group
#            short-summary: Get information about an Azure SQL Database inside of Recommended Elastic Pool.
#            """
helps['sql server'] = """
            type: group
            short-summary: Manage servers.
            """
helps['sql server create'] = """
            type: command
            short-summary: Creates an Azure SQL server.
            """
helps['sql server list'] = """
            type: command
            short-summary: Lists Azure SQL servers.
            """
helps['sql server update'] = """
            type: command
            short-summary: Updates an Azure SQL server.
            """
helps['sql server firewall-rule'] = """
            type: group
            short-summary: Manage Azure SQL server's firewall rules.
            """
#helps['sql server firewall-rule allow-all-azure-ips'] = """
#            type: command
#            short-summary: Create a firewall rule that allows all Azure IP addresses to access the server.
#            """
helps['sql server firewall-rule create'] = """
            type: command
            short-summary: Creates an Azure SQL server firewall rule.
            """
helps['sql server firewall-rule update'] = """
            type: command
            short-summary: Updates an Azure SQL server firewall rule.
            """
helps['sql server firewall-rule show'] = """
            type: command
            short-summary: Shows the details of an Azure SQL server firewall rule.
            """
helps['sql server firewall-rule list'] = """
            type: command
            short-summary: Lists the Azure SQL server firewall rules.
            """
helps['sql server service-objective'] = """
            type: group
            short-summary: Show Azure SQL server's service objectives.
            """
