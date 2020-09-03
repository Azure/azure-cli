# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.rdbms.validators import (
    validate_private_endpoint_connection_id)

from azure.cli.command_modules.rdbms._client_factory import (
    cf_mysql_flexible_servers,
    cf_mysql_flexible_firewall_rules,
    cf_mysql_flexible_config,
    cf_mysql_flexible_db,
    cf_mysql_flexible_replica,
    cf_postgres_flexible_servers,
    cf_postgres_flexible_firewall_rules,
    cf_postgres_flexible_config)

from ._transformers import table_transform_output
# from .transformers import table_transform_connection_string
# from .validators import db_up_namespace_processor

# pylint: disable=too-many-locals, too-many-statements, line-too-long
def load_flexibleserver_command_table(self, _):
    rdbms_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.rdbms.custom#{}')

    ## Flexible server SDKs:
    mysql_flexible_servers_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.rdbms.mysql.flexibleservers.operations#ServersOperations.{}',
        client_factory=cf_mysql_flexible_servers
    )

    mysql_flexible_firewall_rule_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.rdbms.mysql.flexibleservers.operations#FirewallRulesOperations.{}',
        client_factory=cf_mysql_flexible_firewall_rules
    )

    mysql_flexible_config_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.rdbms.mysql.flexibleservers.operations#ConfigurationsOperations.{}',
        client_factory=cf_mysql_flexible_config
    )

    mysql_flexible_db_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.rdbms.mysql.flexibleservers.operations#DatabasesOperations.{}',
        client_factory=cf_mysql_flexible_db
    )

    ''' replica is currently not deployed
    mysql_flexible_replica_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.rdbms.mysql.flexibleservers.operations#ReplicasOperations.{}',
        client_factory=cf_mysql_flexible_replica
    )
    '''

    postgres_flexible_servers_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.rdbms.postgresql.flexibleservers.operations#ServersOperations.{}',
        client_factory=cf_postgres_flexible_servers
    )

    postgres_flexible_firewall_rule_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.rdbms.postgresql.flexibleservers.operations#FirewallRulesOperations.{}',
        client_factory=cf_postgres_flexible_firewall_rules
    )

    postgres_flexible_config_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.rdbms.postgresql.flexibleservers.operations#ConfigurationsOperations.{}',
        client_factory=cf_postgres_flexible_config
    )

    ### MERU COMMANDS
    flexible_server_custom_common = CliCommandType(
        operations_tmpl='azure.cli.command_modules.rdbms.flexible_server_custom_common#{}')
    flexible_servers_custom_postgres = CliCommandType(
        operations_tmpl='azure.cli.command_modules.rdbms.flexible_server_custom_postgres#{}')
    flexible_servers_custom_mysql = CliCommandType(
        operations_tmpl='azure.cli.command_modules.rdbms.flexible_server_custom_mysql#{}')

    ## Postgres commands
    with self.command_group('postgres flexible-server', postgres_flexible_servers_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_servers) as g:
        g.custom_command('create', '_flexible_server_create', table_transformer=table_transform_output)
        g.custom_command('restore', '_flexible_server_restore', supports_no_wait=True)
        g.command('start', 'start')
        g.command('stop', 'stop')
        g.custom_command('delete', '_server_delete_func')
        #g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get')
        g.custom_command('list', '_server_list_custom_func', custom_command_type=flexible_server_custom_common)
        g.generic_update_command('update',
                                 getter_name='_server_update_get', getter_type=rdbms_custom,
                                 setter_name='_server_update_set', setter_type=rdbms_custom,
                                 setter_arg_name='parameters',
                                 custom_func_name='_flexible_server_update_custom_func')
        g.custom_command('reset-password', '_flexible_server_update_password')
        g.custom_wait_command('wait', '_flexible_server_postgresql_get')
        g.command('restart', 'restart')

    with self.command_group('postgres flexible-server firewall-rule', postgres_flexible_firewall_rule_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_firewall_rules) as g:
        g.command('create', 'create_or_update')
        g.custom_command('delete', '_firewall_rule_delete_func', custom_command_type=flexible_server_custom_common)
        # g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')
        # g.custom_command('list', '_flexible_firewall_get_test') # this is setup solely for debugging
        g.generic_update_command('update',
                                 getter_name='_firewall_rule_custom_getter', getter_type=rdbms_custom,
                                 setter_name='_firewall_rule_custom_setter', setter_type=rdbms_custom,
                                 setter_arg_name='parameters',
                                 custom_func_name='_flexible_firewall_rule_update_custom_func',
                                 custom_func_type=flexible_server_custom_common)

    # no custom commands needed
    with self.command_group('postgres flexible-server parameter', postgres_flexible_config_sdk) as g:
        g.custom_command('set', '_flexible_parameter_update')
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')

    ## MySQL commands
    with self.command_group('mysql flexible-server', mysql_flexible_servers_sdk,
                            custom_command_type=flexible_servers_custom_mysql,
                            client_factory=cf_mysql_flexible_servers) as g:
        g.custom_command('create', '_flexible_server_create', table_transformer=table_transform_output)
        g.custom_command('restore', '_flexible_server_restore', supports_no_wait=True)
        g.command('start', 'start')
        g.command('stop', 'stop')
        g.custom_command('delete', '_server_delete_func')
        #g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get')
        g.custom_command('list', '_server_list_custom_func', custom_command_type=flexible_server_custom_common)
        g.generic_update_command('update',
                                 getter_name='_server_update_get', getter_type=rdbms_custom,
                                 setter_name='_server_update_set', setter_type=rdbms_custom,
                                 setter_arg_name='parameters',
                                 custom_func_name='_flexible_server_update_custom_func')
        g.custom_command('reset-password', '_flexible_server_update_password')
        g.custom_wait_command('wait', '_flexible_server_mysql_get')
        g.command('restart', 'restart')

    with self.command_group('mysql flexible-server firewall-rule', mysql_flexible_firewall_rule_sdk,
                            custom_command_type=flexible_servers_custom_mysql,
                            client_factory=cf_mysql_flexible_firewall_rules) as g:
        g.command('create', 'create_or_update')
        g.custom_command('delete', '_firewall_rule_delete_func', custom_command_type=flexible_server_custom_common)
        # g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')
        g.generic_update_command('update',
                                 getter_name='_firewall_rule_custom_getter', getter_type=rdbms_custom,
                                 setter_name='_firewall_rule_custom_setter', setter_type=rdbms_custom,
                                 setter_arg_name='parameters',
                                 custom_func_name='_flexible_firewall_rule_update_custom_func',
                                 custom_func_type=flexible_server_custom_common)

    with self.command_group('mysql flexible-server parameter', mysql_flexible_config_sdk,
                            custom_command_type=flexible_servers_custom_mysql,
                            client_factory=cf_mysql_flexible_config) as g:
        g.custom_command('set', '_flexible_parameter_update')
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')

    with self.command_group('mysql flexible-server db', mysql_flexible_db_sdk) as g:
        g.command('create', 'create_or_update')
        g.custom_command('delete', '_database_delete_func', custom_command_type=flexible_server_custom_common)
        # g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')

    ''' Replica not yet deployed 
    # not working at the moment
    with self.command_group('mysql flexible-server replica', mysql_flexible_replica_sdk) as g:
        g.command('list', 'list_by_server')

    with self.command_group('mysql flexible-server replica', mysql_flexible_servers_sdk,
                            custom_command_type=flexible_servers_custom_mysql,
                            client_factory=cf_mysql_flexible_servers) as g:
        g.custom_command('create', '_flexible_replica_create', supports_no_wait=True)
        g.custom_command('stop', '_flexible_replica_stop', confirmation=True)
    '''
