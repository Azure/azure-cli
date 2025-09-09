# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):
    # Define command types for different operation groups
    migrate_machines_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.migrate.operations#MachinesOperations.{}',
    )

    # Basic migration commands
    with self.command_group('migrate') as g:
        g.custom_command('check-prerequisites', 'check_migration_prerequisites')
        g.custom_command('setup-env', 'setup_migration_environment')
        g.custom_command('verify-setup', 'verify_migrate_setup')

    # Server discovery and replication commands
    with self.command_group('migrate server') as g:
        g.custom_command('list-discovered', 'get_discovered_server')
        g.custom_command('get-discovered-servers-table', 'get_discovered_servers_table')
        g.custom_command('find-by-name', 'get_discovered_servers_by_display_name')
        g.custom_command('create-replication', 'create_server_replication')
        g.custom_command('show-replication-status', 'get_replication_job_status')
        g.custom_command('update-replication', 'set_replication_target_properties')
        g.custom_command('check-environment', 'validate_cross_platform_environment_cmd')

    # Azure Local Migration Commands
    with self.command_group('migrate local') as g:
        g.custom_command('create-disk-mapping', 'create_local_disk_mapping')
        g.custom_command('create-nic-mapping', 'create_local_nic_mapping')
        g.custom_command('create-replication', 'create_local_server_replication')
        g.custom_command('create-replication-with-mappings', 'new_azure_local_server_replication_with_mappings')
        g.custom_command('get-job', 'get_local_replication_job')
        g.custom_command('get-azure-local-job', 'get_azure_local_job')
        g.custom_command('init', 'initialize_local_replication_infrastructure')
        g.custom_command('start-migration', 'start_azure_local_server_migration')
        g.custom_command('remove-replication', 'remove_azure_local_server_replication')

    # PowerShell Module Management Commands  
    with self.command_group('migrate powershell') as g:
        g.custom_command('check-module', 'check_powershell_module')
        g.custom_command('update-modules', 'update_powershell_modules')

    # Authentication commands
    with self.command_group('migrate auth') as g:
        g.custom_command('check', 'check_azure_authentication')
        g.custom_command('login', 'connect_azure_account')
        g.custom_command('logout', 'disconnect_azure_account')
        g.custom_command('set-context', 'set_azure_context')
        g.custom_command('show-context', 'get_azure_context')


