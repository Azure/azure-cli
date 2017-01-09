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
helps['sql server firewall'] = """
            type: group
            short-summary: Commands to manage Azure SQL server's firewall rules
            """
helps['sql server firewall create'] = """
            type: command
            short-summary: Create an Azure SQL server firewall rule
            """
helps['sql server firewall update'] = """
            type: command
            short-summary: Update an Azure SQL server firewall rule
            """
helps['sql server firewall show'] = """
            type: command
            short-summary: Show the details of an Azure SQL server firewall rule
            """
helps['sql server firewall list'] = """
            type: command
            short-summary: List the Azure SQL server firewall rules
            """
helps['sql server service-objective'] = """
            type: group
            short-summary: Commands to show Azure SQL server's service objectives
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
helps['sql elastic-pools'] = """
            type: group
            short-summary: Commands to manage database elastic pools
            """
helps['sql elastic-pools update'] = """
            type: command
            short-summary: Update a database elastic pool
            """
helps['sql elastic-pools database'] = """
            type: command
            short-summary: Command to manage databases activities in database elastic pools
            """
