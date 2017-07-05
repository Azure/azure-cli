# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps


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
                short-summary: Create an {0} server
                examples:
                    - name: Create server testsvr with only required paramaters in North Europe.
                      text: az {1} server create -l northeurope -g testgroup -n testsvr -u username -p password
                    - name: Create server testsvr with specified performance tier and compute units in North Europe.
                      text: az {1} server create -l northeurope -g testgroup -n testsvr -u username -p password --performance-tier Standard --compute-units 100
                    - name: Create server testsvr with all paramaters
                      text: az {1} server create -l northeurope -g testgroup -n testsvr -u username -p password --performance-tier Basic --compute-units 100 --ssl-enforcement Disabled --storage-size 51200 --tags "key=value" --version <server_version>
                """.format(server_type, command_group)
    helps['{} server restore'.format(command_group)] = """
                type: command
                short-summary: Create a new {0} server by restoring from a server backup.
                examples:
                    - name: Restore to server testsvrnew from server testsvr.
                      text: az {1} server restore -g testgroup -n testsvrnew --source-server testsvr --restore-point-in-time "2017-06-15T13:10:00Z"
                    - name: Restore to server testsvrnew from server testsvr2 which is in a different resource group.
                      text: az {1} server restore -g testgroup -n testsvrnew -s "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/othergroup/providers/Microsoft.DBfor{2}/servers/testsvr2" --restore-point-in-time "2017-06-15T13:10:00Z"
                """.format(server_type, command_group, server_type.split()[3])
    helps['{} server update'.format(command_group)] = """
                type: command
                short-summary: Update an {0} server.
                examples:
                    - name: Update server's compute-units to 100.
                      text: az {1} server update -g testgroup -n testsvrnew --compute-units 100
                    - name: Update server's tags.
                      text: az {1} server update -g testgroup -n testsvrnew --tags "k1=v1" "k2=v2"
                """.format(server_type, command_group)
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
                short-summary: List all the {0} servers belong to given resource group or subscription.
                examples:
                    - name: List all servers in resource group.
                      text: az {1} server list -g testgroup
                    - name: List all servers in subscription.
                      text: az {1} server list
                """.format(server_type, command_group)
    helps['{} server firewall-rule'.format(command_group)] = """
                type: group
                short-summary: Commands to manage firewall rules for an %s server
                """ % server_type
    helps['{} server firewall-rule create'.format(command_group)] = """
                type: command
                short-summary: Create a firewall rule for an {0} server
                examples:
                    - name: Create a firewall rule for server testsvr.
                      text: az {1} server firewall-rule create -g testgroup -s testsvr -n allowall --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255
                """.format(server_type, command_group)
    helps['{} server firewall-rule update'.format(command_group)] = """
                type: command
                short-summary: Update a firewall rule for an {0} server
                examples:
                    - name: Update firewall rule's start IP address.
                      text: az {1} server firewall-rule update -g testgroup -s testsvr -n allowall --start-ip-address 0.0.0.1
                    - name: Update firewall rule's start and end IP address.
                      text: az {1} server firewall-rule update -g testgroup -s testsvr -n allowall --start-ip-address 0.0.0.1 --end-ip-address 255.255.255.254
                """.format(server_type, command_group)
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
                short-summary: Update the configuration of an {0} server
                examples:
                    - name: Set new value for a configuration.
                      text: az {1} server configuration set -g testgroup -s testsvr -n <config_name> --value <config_value>
                    - name: Set configuration's value to default.
                      text: az {1} server configuration set -g testgroup -s testsvr -n <config_name>
                """.format(server_type, command_group)
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
    helps['{} server-logs list'.format(command_group)] = """
                type: command
                short-summary: List log files for {0}
                examples:
                    - name: List logs files modified in last 72 hours (default value).
                      text: az {1} server-logs list -g testgroup -s testsvr
                    - name: List logs files modified in last 10 hours.
                      text: az {1} server-logs list -g testgroup -s testsvr --file-last-written 10
                    - name: List logs files that size not exceeds 30KB.
                      text: az {1} server-logs list -g testgroup -s testsvr --max-file-size 30
                """.format(server_type, command_group)
    helps['{} server-logs download'.format(command_group)] = """
                type: command
                short-summary: Download log file(s) to current directory for {0}
                examples:
                    - name: Download log file f1 and f2 for server testsvr.
                      text: az {1} server-logs download -g testgroup -s testsvr -n f1.log f2.log
                """.format(server_type, command_group)
    helps['{} db'.format(command_group)] = """
                type: group
                short-summary: Commands to manage %s databases
                """ % server_type
    helps['{} db create'.format(command_group)] = """
                type: command
                short-summary: Create a database for {0}
                examples:
                    - name: Create database testdb in server testsvr with default parameters.
                      text: az {1} db create -g testgroup -s testsvr -n testdb
                    - name: Create database testdb in server testsvr with specified parameters.
                      text: az {1} db create -g testgroup -s testsvr -n testdb --charset <valid_charset> --collation <valid_collation>
                """.format(server_type, command_group)
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
