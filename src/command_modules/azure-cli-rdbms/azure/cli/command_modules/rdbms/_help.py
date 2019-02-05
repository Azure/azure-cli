# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps

#  pylint: disable=line-too-long


def add_helps(command_group, server_type):
    helps['{}'.format(command_group)] = """
                type: group
                short-summary: Manage Azure Database for {} servers.
                """.format(server_type)
    helps['{} server'.format(command_group)] = """
                type: group
                short-summary: Manage {} servers.
                """.format(server_type)
    helps['{} server create'.format(command_group)] = """
                type: command
                short-summary: Create a server.
                examples:
                    - name: Create a {0} server in North Europe with sku GP_Gen5_2 (General Purpose, Gen 5 hardware, 2 vCores).
                      text: az {1} server create -l northeurope -g testgroup -n testsvr -u username -p password \\
                            --sku-name GP_Gen5_2
                    - name: Create a {0} server with all paramaters set.
                      text: az {1} server create -l northeurope -g testgroup -n testsvr -u username -p password \\
                            --sku-name B_Gen5_1 --ssl-enforcement Disabled \\
                            --backup-retention 10 --geo-redundant-backup Enabled
                            --storage-size 51200 --tags "key=value" --version {{server-version}}
                """.format(server_type, command_group)
    helps['{} server restore'.format(command_group)] = """
                type: command
                short-summary: Restore a server from backup.
                examples:
                    - name: Restore 'testsvr' to a specific point-in-time as a new server 'testsvrnew'.
                      text: az {0} server restore -g testgroup -n testsvrnew --source-server testsvr --restore-point-in-time "2017-06-15T13:10:00Z"
                    - name: Restore 'testsvr2' to 'testsvrnew', where 'testsvrnew' is in a different resource group from 'testsvr2'.
                      text: |
                        az {0} server restore -g testgroup -n testsvrnew \\
                            -s "/subscriptions/${{SubID}}/resourceGroups/${{ResourceGroup}}/providers/Microsoft.DBfor{1}/servers/testsvr2" \\
                            --restore-point-in-time "2017-06-15T13:10:00Z"
                """.format(command_group, server_type)
    helps['{} server georestore'.format(command_group)] = """
                type: command
                short-summary: Geo-restore a server from backup.
                examples:
                    - name: Geo-restore 'testsvr' into a new server 'testsvrnew' located in West US 2.
                      text: az {0} server georestore -g testgroup -n testsvrnew --source-server testsvr -l westus2
                    - name: Geo-restore 'testsvr' into a new server 'testsvrnew' located in West US 2 with sku GP_Gen5_2.
                      text: az {0} server georestore -g testgroup -n testsvrnew --source-server testsvr -l westus2 --sku-name GP_Gen5_2
                    - name: Geo-restore 'testsvr2' into a new server 'testsvrnew', where 'testsvrnew' is in a different resource group from 'testsvr2'.
                      text: |
                        az {0} server georestore -g testgroup -n testsvrnew \\
                            -s "/subscriptions/${{SubID}}/resourceGroups/${{ResourceGroup}}/providers/Microsoft.DBfor{1}/servers/testsvr2" \\
                            -l westus2
                """.format(command_group, server_type)
    helps['mysql server replica'] = """
                type: group
                short-summary: Manage read replicas.
                """
    helps['mysql server replica create'] = """
                type: command
                short-summary: Create a read replica for a server.
                examples:
                    - name: Create a read replica 'testreplsvr' for 'testsvr'.
                      text: az mysql server replica create -n testreplsvr -g testgroup -s testsvr
                    - name: Create a read replica 'testreplsvr' for 'testsvr2', where 'testreplsvr' is in a different resource group.
                      text: |
                        az mysql server replica create -n testreplsvr -g testgroup \\
                            -s "/subscriptions/${SubID}/resourceGroups/${ResourceGroup}/providers/Microsoft.DBforMySQL/servers/testsvr2"
                """
    helps['mysql server replica stop'] = """
                type: command
                short-summary: Stop replication to a read replica and make it a read/write server.
                examples:
                    - name: Stop replication to 'testreplsvr' and make it a read/write server.
                      text: az mysql server replica stop -g testgroup -n testreplsvr
                """
    helps['mysql server replica list'] = """
                type: command
                short-summary: List all read replicas for a given server.
                examples:
                    - name: List all read replicas for master server 'testsvr'.
                      text: az mysql server replica list -g testgroup -s testsvr
                """
    helps['{} server update'.format(command_group)] = """
                type: command
                short-summary: Update a server.
                examples:
                    - name: Update a server's sku.
                      text: az {0} server update -g testgroup -n testsvrnew --sku-name GP_Gen5_4
                    - name: Update a server's tags.
                      text: az {0} server update -g testgroup -n testsvrnew --tags "k1=v1" "k2=v2"
                """.format(command_group)
    helps['{} server wait'.format(command_group)] = """
                type: command
                short-summary: Wait for server to satisfy certain conditions.
                """
    helps['{} server delete'.format(command_group)] = """
                type: command
                short-summary: Delete a server.
                examples:
                    - name: Delete a server.
                      text: az {0} server delete -g testgroup -n testsvr
                """.format(command_group)
    helps['{} server show'.format(command_group)] = """
                type: command
                short-summary: Get the details of a server.
                """
    helps['{} server list'.format(command_group)] = """
                type: command
                short-summary: List available servers.
                examples:
                    - name: List all {0} servers in a subscription.
                      text: az {1} server list
                    - name: List all {0} servers in a resource group.
                      text: az {1} server list -g testgroup
                """.format(server_type, command_group)
    helps['{} server firewall-rule'.format(command_group)] = """
                type: group
                short-summary: Manage firewall rules for a server.
                """
    helps['{} server firewall-rule create'.format(command_group)] = """
                type: command
                short-summary: Create a new firewall rule for a server.
                examples:
                    - name: Create a firewall rule allowing connections from a specific IP address.
                      text: az {0} server firewall-rule create -g testgroup -s testsvr -n allowip --start-ip-address 107.46.14.221 --end-ip-address 107.46.14.221
                    - name: Create a firewall rule allowing connections from an IP address range.
                      text: az {0} server firewall-rule create -g testgroup -s testsvr -n allowiprange --start-ip-address 107.46.14.0 --end-ip-address 107.46.14.221
                """.format(command_group)
    helps['{} server firewall-rule update'.format(command_group)] = """
                type: command
                short-summary: Update a firewall rule.
                examples:
                    - name: Update a firewall rule's start IP address.
                      text: az {0} server firewall-rule update -g testgroup -s testsvr -n allowiprange --start-ip-address 107.46.14.1
                    - name: Update a firewall rule's start and end IP address.
                      text: az {0} server firewall-rule update -g testgroup -s testsvr -n allowiprange --start-ip-address 107.46.14.2 --end-ip-address 107.46.14.218
                """.format(command_group)
    helps['{} server firewall-rule delete'.format(command_group)] = """
                type: command
                short-summary: Delete a firewall rule.
                """
    helps['{} server firewall-rule show'.format(command_group)] = """
                type: command
                short-summary: Get the details of a firewall rule.
                """
    helps['{} server firewall-rule list'.format(command_group)] = """
                type: command
                short-summary: List all firewall rules for a server.
                """

    helps['{} server vnet-rule'.format(command_group)] = """
                type: group
                short-summary: Manage a server's virtual network rules.
                """
    helps['{} server vnet-rule update'.format(command_group)] = """
                type: command
                short-summary: Update a virtual network rule.
                """
    helps['{} server vnet-rule create'.format(command_group)] = """
                type: command
                short-summary: Create a virtual network rule to allows access to a {} server.
                examples:
                    - name: Create a virtual network rule by providing the subnet id.
                      text: az {} server vnet-rule create -g testgroup -s testsvr -n vnetRuleName --subnet /subscriptions/{{SubID}}/resourceGroups/{{ResourceGroup}}/providers/Microsoft.Network/virtualNetworks/vnetName/subnets/subnetName
                    - name: Create a vnet rule by providing the vnet and subnet name. The subnet id is created by taking the resource group name and subscription id of the server.
                      text: az {} server vnet-rule create -g testgroup -s testsvr -n vnetRuleName --subnet subnetName --vnet-name vnetName
                """.format(server_type, command_group, command_group)

    helps['{} server configuration'.format(command_group)] = """
                type: group
                short-summary: Manage configuration values for a server.
                """
    helps['{} server configuration set'.format(command_group)] = """
                type: command
                short-summary: Update the configuration of a server.
                examples:
                    - name: Set a new configuration value.
                      text: az {0} server configuration set -g testgroup -s testsvr -n {{config_name}} --value {{config_value}}
                    - name: Set a configuration value to its default.
                      text: az {0} server configuration set -g testgroup -s testsvr -n {{config_name}}
                """.format(command_group)
    helps['{} server configuration show'.format(command_group)] = """
                type: command
                short-summary: Get the configuration for a server."
                """
    helps['{} server configuration list'.format(command_group)] = """
                type: command
                short-summary: List the configuration values for a server.
                """
    helps['{} server-logs'.format(command_group)] = """
                type: group
                short-summary: Manage server logs.
                """
    helps['{} server-logs list'.format(command_group)] = """
                type: command
                short-summary: List log files for a server.
                examples:
                    - name: List log files for 'testsvr' modified in the last 72 hours (default value).
                      text: az {0} server-logs list -g testgroup -s testsvr
                    - name: List log files for 'testsvr' modified in the last 10 hours.
                      text: az {0} server-logs list -g testgroup -s testsvr --file-last-written 10
                    - name: List log files for 'testsvr' less than 30Kb in size.
                      text: az {0} server-logs list -g testgroup -s testsvr --max-file-size 30
                """.format(command_group)
    helps['{} server-logs download'.format(command_group)] = """
                type: command
                short-summary: Download log files.
                examples:
                    - name: Download log files f1 and f2 to the current directory from the server 'testsvr'.
                      text: az {} server-logs download -g testgroup -s testsvr -n f1.log f2.log
                """.format(command_group)
    helps['{} db'.format(command_group)] = """
                type: group
                short-summary: Manage {0} databases on a server.
                """.format(server_type)
    helps['{} db create'.format(command_group)] = """
                type: command
                short-summary: Create a {0} database.
                examples:
                    - name: Create database 'testdb' in the server 'testsvr' with the default parameters.
                      text: az {1} db create -g testgroup -s testsvr -n testdb
                    - name: Create database 'testdb' in server 'testsvr' with a given character set and collation rules.
                      text: az {1} db create -g testgroup -s testsvr -n testdb --charset {{valid_charset}} --collation {{valid_collation}}
                """.format(server_type, command_group)
    helps['{} db delete'.format(command_group)] = """
                type: command
                short-summary: Delete a database.
                examples:
                    - name: Delete database 'testdb' in the server 'testsvr'.
                      text: az {0} db delete -g testgroup -s testsvr -n testdb
                """.format(command_group)
    helps['{} db show'.format(command_group)] = """
                type: command
                short-summary: Show the details of a database.
                examples:
                    - name: Show database 'testdb' in the server 'testsvr'.
                      text: az {0} db show -g testgroup -s testsvr -n testdb
                """.format(command_group)
    helps['{} db list'.format(command_group)] = """
                type: command
                short-summary: List the databases for a server.
                examples:
                    - name: List databases in the server 'testsvr'.
                      text: az {0} db list -g testgroup -s testsvr
                """.format(command_group)


add_helps("mariadb", "MariaDB")
add_helps("mysql", "MySQL")
add_helps("postgres", "PostgreSQL")
