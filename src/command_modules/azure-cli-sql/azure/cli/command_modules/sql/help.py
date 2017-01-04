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
helps['sql server list'] = """
            type: command
            short-summary: List the SQL Server belongs to given resource grounp
            """
