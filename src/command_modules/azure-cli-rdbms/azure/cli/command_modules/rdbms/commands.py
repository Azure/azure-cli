# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.sdk.util import (
    create_service_adapter,
    ServiceGroup)
from ._util import (
    get_mysql_management_client,
    get_postgresql_management_client)

custom_path = 'azure.cli.command_modules.rdbms.custom#{}'


def load_commands_from_factory(server_type, command_group_name, management_client):
    # server
    server_sa = create_service_adapter(
        'azure.mgmt.rdbms.{}.operations.servers_operations'.format(server_type),
        'ServersOperations')

    def server_factory(args):
        return management_client(args).servers

    with ServiceGroup(__name__, server_factory, server_sa, custom_path) as s:
        with s.group('{} server'.format(command_group_name)) as c:
            c.command('create', 'create_or_update')
            c.custom_command('restore', '_server_restore')
            c.command('delete', 'delete', confirmation=True)
            c.command('show', 'get')
            c.custom_command('list', '_server_list_custom_func')
            c.generic_update_command('update', 'get', 'update',
                                     custom_func_name='_server_update_custom_func')

    # firewall rule
    firewall_rule_sa = create_service_adapter(
        'azure.mgmt.rdbms.{}.operations.firewall_rules_operations'.format(server_type),
        'FirewallRulesOperations')

    def firewall_rule_factory(args):
        return management_client(args).firewall_rules

    with ServiceGroup(__name__, firewall_rule_factory, firewall_rule_sa, custom_path) as s:
        with s.group('{} server firewall-rule'.format(command_group_name)) as c:
            c.command('create', 'create_or_update')
            c.command('delete', 'delete', confirmation=True)
            c.command('show', 'get')
            c.command('list', 'list_by_server')
    cli_generic_update_command(__name__,
                               '{} server firewall-rule update'.format(command_group_name),
                               firewall_rule_sa('get'),
                               custom_path.format('_firewall_rule_custom_setter'),
                               firewall_rule_factory,
                               custom_function_op=custom_path.format('_firewall_rule_update_custom_func'))

    # configuration
    configuration_sa = create_service_adapter(
        'azure.mgmt.rdbms.{}.operations.configurations_operations'.format(server_type),
        'ConfigurationsOperations')

    def configuration_factory(args):
        return management_client(args).configurations

    with ServiceGroup(__name__, configuration_factory, configuration_sa) as s:
        with s.group('{} server configuration'.format(command_group_name)) as c:
            c.command('set', 'create_or_update')
            c.command('show', 'get')
            c.command('list', 'list_by_server')

    # log_files
    log_file_sa = create_service_adapter(
        'azure.mgmt.rdbms.{}.operations.log_files_operations'.format(server_type),
        'LogFilesOperations')

    def log_file_factory(args):
        return management_client(args).log_files

    with ServiceGroup(__name__, log_file_factory, log_file_sa, custom_path) as s:
        with s.group('{} server-logs'.format(command_group_name)) as c:
            c.custom_command('list', '_list_log_files_with_filter')
            c.custom_command('download', '_download_log_files')

    # database
    database_sa = create_service_adapter(
        'azure.mgmt.rdbms.{}.operations.databases_operations'.format(server_type),
        'DatabasesOperations')

    def database_factory(args):
        return management_client(args).databases

    with ServiceGroup(__name__, database_factory, database_sa) as s:
        with s.group('{} db'.format(command_group_name)) as c:
            # c.command('create', 'create_or_update')
            # c.command('delete', 'delete', confirmation=True)
            # c.command('show', 'get')
            c.command('list', 'list_by_server')


load_commands_from_factory('mysql', 'mysql', get_mysql_management_client)
load_commands_from_factory('postgresql', 'postgres', get_postgresql_management_client)
