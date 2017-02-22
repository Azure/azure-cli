# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long

helps['sql'] = """
            type: group
            short-summary: Commands to manage Azure SQL databases.
            """
helps['sql db'] = """
            type: group
            short-summary: Commands to manage databases
            """
helps['sql db create'] = """
            type: command
            short-summary: Create an Azure SQL database
            """
helps['sql db replication-link'] = """
            type: group
            short-summary: Manage database replication links
            """
helps['sql db data-warehouse'] = """
            type: group
            short-summary: Manage database data warehouse
            """
helps['sql db restore-point'] = """
            type: group
            short-summary: Manage database restore points
            """
helps['sql db transparent-data-encryption'] = """
            type: group
            short-summary: Manage database transparent data encryption
            """
helps['sql db service-tier-advisor'] = """
            type: group
            short-summary: Manage database service tier advisors
            """
helps['sql elastic-pool'] = """
            type: group
            short-summary: Commands to manage database elastic pools
            """
helps['sql elastic-pool update'] = """
            type: command
            short-summary: Update a database elastic pool
            """
helps['sql elastic-pool db'] = """
            type: group
            short-summary: Command to manage databases activities in database elastic pools
            """
helps['sql elastic-pool recommended'] = """
            type: group
            short-summary: Commands to see information about an Azure SQL Recommended Elastic Pool
            """
helps['sql elastic-pool recommended db'] = """
            type: group
            short-summary: Commands to see information about an Azure SQL database inside of Recommended Elastic Pool
            """
helps['sql server'] = """
            type: group
            short-summary: Commands to manage servers.
            """
helps['sql server create'] = """
            type: command
            short-summary: Create a new Azure SQL server
            """
helps['sql server list'] = """
            type: command
            short-summary: List the SQL servers belong to given resource group.
            """
helps['sql server update'] = """
            type: command
            short-summary: Update an Azure SQL server.
            """
helps['sql server firewall-rule'] = """
            type: group
            short-summary: Commands to manage Azure SQL server's firewall rules
            """
helps['sql server firewall-rule allow-all-azure-ips'] = """
            type: command
            short-summary: Create a firewall rule that allows all Azure IP addresses to access the server
            """
helps['sql server firewall-rule create'] = """
            type: command
            short-summary: Create a firewall rule that allows an IP address range to access the server
            """
helps['sql server firewall-rule update'] = """
            type: command
            short-summary: Update firewall rule
            """
helps['sql server firewall-rule show'] = """
            type: command
            short-summary: Show the details of firewall rule
            """
helps['sql server firewall-rule list'] = """
            type: command
            short-summary: List firewall rules
            """
helps['sql server service-objective'] = """
            type: group
            short-summary: Commands to show Azure SQL server's service objectives
            """