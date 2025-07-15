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
        
    with self.command_group('migrate plan') as g:
        g.custom_command('create', 'create_migration_plan')
        g.custom_command('list', 'list_migration_plans')
        g.custom_command('show', 'get_migration_status')
        g.custom_command('execute-step', 'execute_migration_step')

    with self.command_group('migrate assess') as g:
        g.custom_command('sql-server', 'assess_sql_server')
        g.custom_command('hyperv-vm', 'assess_hyperv_vm')
        g.custom_command('filesystem', 'assess_filesystem')
        g.custom_command('network', 'assess_network')

    with self.command_group('migrate powershell') as g:
        g.custom_command('execute', 'execute_custom_powershell')

    with self.command_group('migrate', is_preview=True):
        pass

    # Azure CLI equivalents to PowerShell Az.Migrate commands
    with self.command_group('migrate server') as g:
        g.custom_command('list-discovered', 'get_discovered_server')
        g.custom_command('start-replication', 'new_server_replication')
        g.custom_command('show-replication', 'get_server_replication')
        g.custom_command('start-migration', 'start_server_migration')
        g.custom_command('stop-replication', 'remove_server_replication')
        g.custom_command('show-replication-by-id', 'get_server_replication_by_id')
        g.custom_command('start-migration-with-object', 'start_server_migration_with_object')

    with self.command_group('migrate job') as g:
        g.custom_command('show', 'get_migration_job')
        g.custom_command('show-local', 'get_local_job')

    with self.command_group('migrate project') as g:
        g.custom_command('create', 'create_migrate_project')

    with self.command_group('migrate infrastructure') as g:
        g.custom_command('initialize', 'initialize_replication_infrastructure')

    with self.command_group('migrate disk') as g:
        g.custom_command('create-mapping', 'create_disk_mapping')

    with self.command_group('migrate replication') as g:
        g.custom_command('create-with-params', 'create_server_replication_with_params')

    with self.command_group('migrate auth') as g:
        g.custom_command('check', 'check_azure_authentication')
        g.custom_command('login', 'connect_azure_account')
        g.custom_command('logout', 'disconnect_azure_account')
        g.custom_command('set-context', 'set_azure_context')
        g.custom_command('show-context', 'get_azure_context')

