# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.migrate._client_factory import cf_migrate


def load_command_table(self, _):

    with self.command_group('migrate') as g:
        g.custom_command('check-prerequisites', 'check_migration_prerequisites')
        g.custom_command('setup-env', 'setup_migration_environment')

    # Azure CLI equivalents to PowerShell Az.Migrate commands
    with self.command_group('migrate server') as g:
        g.custom_command('list-discovered', 'get_discovered_server')
        g.custom_command('list-discovered-table', 'get_discovered_servers_table')
        
        # New Azure Migrate server replication commands
        g.custom_command('find-by-name', 'get_discovered_servers_by_display_name')
        g.custom_command('create-replication', 'create_server_replication')
        g.custom_command('create-replication-by-index', 'create_server_replication_by_index')
        g.custom_command('create-bulk-replication', 'create_multiple_server_replications')
        g.custom_command('show-replication-status', 'get_replication_job_status')
        g.custom_command('update-replication', 'set_replication_target_properties')

    with self.command_group('migrate infrastructure') as g:
        g.custom_command('initialize', 'initialize_replication_infrastructure')

    with self.command_group('migrate auth') as g:
        g.custom_command('check', 'check_azure_authentication')
        g.custom_command('login', 'connect_azure_account')
        g.custom_command('logout', 'disconnect_azure_account')
        g.custom_command('set-context', 'set_azure_context')
        g.custom_command('show-context', 'get_azure_context')

    # Azure CLI equivalents to PowerShell Az.Storage commands
    with self.command_group('migrate storage') as g:
        g.custom_command('get-account', 'get_storage_account')
        g.custom_command('list-accounts', 'list_storage_accounts')
        g.custom_command('show-account-details', 'show_storage_account_details')

