# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.help_files import helps


def add_helps(commnad_group, server_type):
    helps['{}'.format(commnad_group)] = """
                type: group
                short-summary: Commands to manage Azure %s servers.
                """ % server_type
    helps['{} server'.format(commnad_group)] = """
                type: group
                short-summary: Commands to manage %s servers.
                """ % server_type
    helps['{} server create'.format(commnad_group)] = """
                type: command
                short-summary: Creates a new %s server
                """ % server_type
    helps['{} server update'.format(commnad_group)] = """
                type: command
                short-summary: Updates a %s server.
                """ % server_type
    helps['{} server delete'.format(commnad_group)] = """
                type: command
                short-summary: Deletes a %s server.
                """ % server_type
    helps['{} server show'.format(commnad_group)] = """
                type: command
                short-summary: Show the details of a %s server.
                """ % server_type
    helps['{} server list'.format(commnad_group)] = """
                type: command
                short-summary: List all the %s servers belong to given resource group.
                """ % server_type
    helps['{} server firewall-rule'.format(commnad_group)] = """
                type: group
                short-summary: Commands to manage Azure %s server's firewall rules
                """ % server_type
    helps['{} server firewall-rule create'.format(commnad_group)] = """
                type: command
                short-summary: Creates a firewall rule
                """
    helps['{} server firewall-rule update'.format(commnad_group)] = """
                type: command
                short-summary: Updates a firewall rule
                """
    helps['{} server firewall-rule delete'.format(commnad_group)] = """
                type: command
                short-summary: Deletes a firewall rule
                """
    helps['{} server firewall-rule show'.format(commnad_group)] = """
                type: command
                short-summary: Show the details of a firewall rule
                """
    helps['{} server firewall-rule list'.format(commnad_group)] = """
                type: command
                short-summary: List all the firewall rules of a given server
                """
    helps['{} server configuration'.format(commnad_group)] = """
                type: group
                short-summary: Commands to manage %s server configurations
                """ % server_type
    helps['{} server configuration set'.format(commnad_group)] = """
                type: command
                short-summary: Updates the value of a server configuration
                """
    helps['{} server configuration show'.format(commnad_group)] = """
                type: command
                short-summary: Show the details of a server configuration
                """
    helps['{} server configuration list'.format(commnad_group)] = """
                type: command
                short-summary: List all the configurations of a given server
                """
    helps['{} server-logs'.format(commnad_group)] = """
                type: group
                short-summary: Commands to manage %s server logs.
                """ % server_type
    helps['{} db'.format(commnad_group)] = """
                type: group
                short-summary: Commands to manage %s databases
                """ % server_type
    helps['{} db create'.format(commnad_group)] = """
                type: command
                short-summary: Creates a database
                """
    helps['{} db delete'.format(commnad_group)] = """
                type: command
                short-summary: Deletes a database
                """
    helps['{} db show'.format(commnad_group)] = """
                type: command
                short-summary: Show the details of a database
                """
    helps['{} db list'.format(commnad_group)] = """
                type: command
                short-summary: List all the databases of a given server
                """


add_helps("mysql", "MySQL")
add_helps("postgres", "PostgreSQL")
