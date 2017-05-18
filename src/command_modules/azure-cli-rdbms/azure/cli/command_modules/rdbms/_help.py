# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


def add_helps(command_group, server_type):
    helps['{}'.format(command_group)] = """
                type: group
                short-summary: Commands to manage %s servers.
                """ % server_type
    helps['{} server'.format(command_group)] = """
                type: group
                short-summary: Commands to manage %s servers.
                """ % server_type
    helps['{} server create'.format(command_group)] = """
                type: command
                short-summary: Create an %s server
                """ % server_type
    helps['{} server update'.format(command_group)] = """
                type: command
                short-summary: Update an %s server.
                """ % server_type
    helps['{} server delete'.format(command_group)] = """
                type: command
                short-summary: Delete an %s server.
                """ % server_type
    helps['{} server show'.format(command_group)] = """
                type: command
                short-summary: Show the details of an %s server.
                """ % server_type
    helps['{} server list'.format(command_group)] = """
                type: command
                short-summary: List all the %s servers belong to given resource group.
                """ % server_type
    helps['{} server firewall-rule'.format(command_group)] = """
                type: group
                short-summary: Commands to manage firewall rules for an %s server
                """ % server_type
    helps['{} server firewall-rule create'.format(command_group)] = """
                type: command
                short-summary: Create a firewall rule for an %s server
                """ % server_type
    helps['{} server firewall-rule update'.format(command_group)] = """
                type: command
                short-summary: Update a firewall rule for an %s server
                """ % server_type
    helps['{} server firewall-rule delete'.format(command_group)] = """
                type: command
                short-summary: Delete a firewall rule for an %s server
                """ % server_type
    helps['{} server firewall-rule show'.format(command_group)] = """
                type: command
                short-summary: Show the details of a firewall rule for an %s server
                """ % server_type
    helps['{} server firewall-rule list'.format(command_group)] = """
                type: command
                short-summary: List all the firewall rules for an %s server
                """ % server_type
    helps['{} server configuration'.format(command_group)] = """
                type: group
                short-summary: Commands to configure an %s server
                """ % server_type
    helps['{} server configuration set'.format(command_group)] = """
                type: command
                short-summary: Update the configuration of an %s server
                """ % server_type
    helps['{} server configuration show'.format(command_group)] = """
                type: command
                short-summary: Show the configuration of an %s server
                """ % server_type
    helps['{} server configuration list'.format(command_group)] = """
                type: command
                short-summary: List the configurations of an %s server
                """ % server_type
    helps['{} server-logs'.format(command_group)] = """
                type: group
                short-summary: Commands to manage %s server logs.
                """ % server_type
    helps['{} db'.format(command_group)] = """
                type: group
                short-summary: Commands to manage %s databases
                """ % server_type
    helps['{} db create'.format(command_group)] = """
                type: command
                short-summary: Create a database for %s
                """ % server_type
    helps['{} db delete'.format(command_group)] = """
                type: command
                short-summary: Delete a database for %s
                """ % server_type
    helps['{} db show'.format(command_group)] = """
                type: command
                short-summary: Show the details of a database for %s
                """ % server_type
    helps['{} db list'.format(command_group)] = """
                type: command
                short-summary: List the databases of an %s server
                """ % server_type


add_helps("mysql", "Azure Database for MySQL")
add_helps("postgres", "Azure Database for PostgreSQL")
