# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
import azure.cli.command_modules.documentdb
from azure.cli.command_modules.documentdb._client_factory import (cf_documentdb)

cli_command(__name__, 'documentdb show', 'azure.cli.command_modules.documentdb.sdk.operations.database_accounts_operations#DatabaseAccountsOperations.get', cf_documentdb)
cli_command(__name__, 'documentdb list', 'azure.cli.command_modules.documentdb.sdk.operations.database_accounts_operations#DatabaseAccountsOperations.list_by_resource_group', cf_documentdb)
cli_command(__name__, 'documentdb list-all', 'azure.cli.command_modules.documentdb.sdk.operations.database_accounts_operations#DatabaseAccountsOperations.list', cf_documentdb)
cli_command(__name__, 'documentdb list-keys', 'azure.cli.command_modules.documentdb.sdk.operations.database_accounts_operations#DatabaseAccountsOperations.list_keys', cf_documentdb)
cli_command(__name__, 'documentdb list-read-only-keys', 'azure.cli.command_modules.documentdb.sdk.operations.database_accounts_operations#DatabaseAccountsOperations.list_read_only_keys', cf_documentdb)
cli_command(__name__, 'documentdb regenerate-key', 'azure.cli.command_modules.documentdb.sdk.operations.database_accounts_operations#DatabaseAccountsOperations.regenerate_key', cf_documentdb)
cli_command(__name__, 'documentdb check-name-exists', 'azure.cli.command_modules.documentdb.sdk.operations.database_accounts_operations#DatabaseAccountsOperations.check_name_exists', cf_documentdb)
cli_command(__name__, 'documentdb delete', 'azure.cli.command_modules.documentdb.sdk.operations.database_accounts_operations#DatabaseAccountsOperations.delete', cf_documentdb)
cli_command(__name__, 'documentdb failover-priority-change', 'azure.cli.command_modules.documentdb.sdk.operations.database_accounts_operations#DatabaseAccountsOperations.failover_priority_change', cf_documentdb)
cli_command(__name__, 'documentdb create', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_create', cf_documentdb)
