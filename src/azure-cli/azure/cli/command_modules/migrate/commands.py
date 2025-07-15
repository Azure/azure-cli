# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.migrate._client_factory import cf_migrate


def load_command_table(self, _):

    migrate_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.migrate.custom#{}',
        client_factory=cf_migrate)

    with self.command_group('migrate') as g:
        g.custom_command('check-prerequisites', 'check_migration_prerequisites')
        g.custom_command('discover', 'discover_migration_sources')
        g.custom_command('assess', 'assess_migration_readiness')
        g.custom_command('setup-env', 'setup_migration_environment')

    # Azure CLI equivalents to PowerShell Az.Migrate commands
    with self.command_group('migrate server') as g:
        g.custom_command('list-discovered', 'get_discovered_server')
        g.custom_command('list-discovered-table', 'get_discovered_servers_table')
        g.custom_command('start-replication', 'new_server_replication')
        g.custom_command('show-replication', 'get_server_replication')
        g.custom_command('start-migration', 'start_server_migration')
        g.custom_command('stop-replication', 'remove_server_replication')

    with self.command_group('migrate job') as g:
        g.custom_command('show', 'get_migration_job')

    with self.command_group('migrate project') as g:
        g.custom_command('create', 'create_migrate_project')

    with self.command_group('migrate infrastructure') as g:
        g.custom_command('initialize', 'initialize_replication_infrastructure')

    # Add auth commands back when implemented
    # with self.command_group('migrate auth') as g:
    #     g.custom_command('check', 'check_azure_authentication')
    #     g.custom_command('login', 'connect_azure_account')
    #     g.custom_command('logout', 'disconnect_azure_account')
    #     g.custom_command('set-context', 'set_azure_context')
    #     g.custom_command('show-context', 'get_azure_context')

