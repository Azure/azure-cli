# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):
    # Define command types for different operation groups
    migrate_projects_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.migrate.operations#ProjectsOperations.{}',
    )

    migrate_assessments_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.migrate.operations#AssessmentsOperations.{}',
    )

    migrate_machines_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.migrate.operations#MachinesOperations.{}',
    )

    # Basic migration commands
    with self.command_group('migrate') as g:
        g.custom_command('check-prerequisites', 'check_migration_prerequisites')
        g.custom_command('setup-env', 'setup_migration_environment')

    # Server discovery and replication commands
    with self.command_group('migrate server') as g:
        g.custom_command('list-discovered', 'get_discovered_server')
        g.custom_command('list-discovered-table', 'get_discovered_servers_table')
        g.custom_command('find-by-name', 'get_discovered_servers_by_display_name')
        g.custom_command('create-replication', 'create_server_replication')
        g.custom_command('show-replication-status', 'get_replication_job_status')
        g.custom_command('update-replication', 'set_replication_target_properties')

    # Azure Migrate project management
    with self.command_group('migrate project', migrate_projects_sdk) as g:
        g.custom_command('create', 'create_migrate_project')
        g.custom_command('delete', 'delete_migrate_project')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_migrate_projects')

    # Assessment management
    with self.command_group('migrate assessment', migrate_assessments_sdk) as g:
        g.custom_command('create', 'create_assessment')
        g.custom_command('list', 'list_assessments')
        g.show_command('show', 'get')
        g.custom_command('delete', 'delete_assessment')

    # Machine management
    with self.command_group('migrate machine', migrate_machines_sdk) as g:
        g.custom_command('list', 'list_machines')
        g.show_command('show', 'get')

    # Azure Stack HCI Local Migration Commands
    with self.command_group('migrate local') as g:
        g.custom_command('create-disk-mapping', 'create_local_disk_mapping')
        g.custom_command('create-replication', 'create_local_server_replication')
        g.custom_command('create-replication-advanced', 'create_local_server_replication_advanced')
        g.custom_command('get-job', 'get_local_replication_job')
        g.custom_command('init-infrastructure', 'initialize_local_replication_infrastructure')

    # Azure Resource Management Commands
    with self.command_group('migrate resource') as g:
        g.custom_command('list-groups', 'list_resource_groups')

    # PowerShell Module Management Commands  
    with self.command_group('migrate powershell') as g:
        g.custom_command('check-module', 'check_powershell_module')

    # Infrastructure management
    with self.command_group('migrate infrastructure') as g:
        g.custom_command('init', 'initialize_replication_infrastructure')
        g.custom_command('check', 'check_replication_infrastructure')

    # Authentication commands
    with self.command_group('migrate auth') as g:
        g.custom_command('check', 'check_azure_authentication')
        g.custom_command('login', 'connect_azure_account')
        g.custom_command('logout', 'disconnect_azure_account')
        g.custom_command('set-context', 'set_azure_context')
        g.custom_command('show-context', 'get_azure_context')

    # Azure Storage commands
    with self.command_group('migrate storage') as g:
        g.custom_command('get-account', 'get_storage_account')
        g.custom_command('list-accounts', 'list_storage_accounts')
        g.custom_command('show-account-details', 'show_storage_account_details')

