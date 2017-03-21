# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.documentdb._client_factory import (cf_documentdb)

custom_path = 'azure.mgmt.documentdb.operations.database_accounts_operations#{}'

cli_command(__name__, 'documentdb show', custom_path.format('DatabaseAccountsOperations.get'), cf_documentdb)
cli_command(__name__, 'documentdb list-keys', custom_path.format('DatabaseAccountsOperations.list_keys'), cf_documentdb)
cli_command(__name__, 'documentdb list-read-only-keys', custom_path.format('DatabaseAccountsOperations.list_read_only_keys'), cf_documentdb)
cli_command(__name__, 'documentdb regenerate-key', custom_path.format('DatabaseAccountsOperations.regenerate_key'), cf_documentdb)
cli_command(__name__, 'documentdb check-name-exists', custom_path.format('DatabaseAccountsOperations.check_name_exists'), cf_documentdb)
cli_command(__name__, 'documentdb delete', custom_path.format('DatabaseAccountsOperations.delete'), cf_documentdb)
cli_command(__name__, 'documentdb failover-priority-change', custom_path.format('DatabaseAccountsOperations.failover_priority_change'), cf_documentdb)
cli_command(__name__, 'documentdb create', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_create', cf_documentdb)
cli_command(__name__, 'documentdb update', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_update', cf_documentdb)
cli_command(__name__, 'documentdb list', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_list', cf_documentdb)
