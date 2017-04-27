# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.documentdb._client_factory import (cf_documentdb)

mgmt_path = 'azure.mgmt.documentdb.operations.database_accounts_operations#{}'

def db_accounts_factory(_):
    return cf_documentdb().database_accounts

cli_command(__name__, 'documentdb show', mgmt_path.format('DatabaseAccountsOperations.get'), db_accounts_factory)
cli_command(__name__, 'documentdb list-keys', mgmt_path.format('DatabaseAccountsOperations.list_keys'), db_accounts_factory)
cli_command(__name__, 'documentdb list-read-only-keys', mgmt_path.format('DatabaseAccountsOperations.list_read_only_keys'), db_accounts_factory)
cli_command(__name__, 'documentdb list-connection-strings', mgmt_path.format('DatabaseAccountsOperations.list_connection_strings'), db_accounts_factory)
cli_command(__name__, 'documentdb regenerate-key', mgmt_path.format('DatabaseAccountsOperations.regenerate_key'), db_accounts_factory)
cli_command(__name__, 'documentdb check-name-exists', mgmt_path.format('DatabaseAccountsOperations.check_name_exists'), db_accounts_factory)
cli_command(__name__, 'documentdb delete', mgmt_path.format('DatabaseAccountsOperations.delete'), db_accounts_factory)
cli_command(__name__, 'documentdb failover-priority-change', mgmt_path.format('DatabaseAccountsOperations.failover_priority_change'), db_accounts_factory)
cli_command(__name__, 'documentdb create', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_create', db_accounts_factory)
cli_command(__name__, 'documentdb update', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_update', db_accounts_factory)
cli_command(__name__, 'documentdb list', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_list', db_accounts_factory)
