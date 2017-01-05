# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps

# pylint: disable=line-too-long

helps['sql'] = """
            type: group
            short-summary: Commands to manage Azure SQL Servers.
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
            short-summary: List the SQL Server belongs to given resource group.
            """
helps['sql server update'] = """
            type: command
            short-summary: Update a Azure SQL server.
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
            short-summary: Commands to manage Azure SQL server's service objectives
            """
