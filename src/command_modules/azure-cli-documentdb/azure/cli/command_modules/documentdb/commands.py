# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.documentdb._client_factory import (cf_documentdb)

mgmt_path = 'azure.mgmt.documentdb.operations.database_accounts_operations#{}'

factory = lambda kwargs: cf_documentdb().database_accounts  # noqa: E731 lambda vs def
cli_command(__name__, 'documentdb show', mgmt_path.format('DatabaseAccountsOperations.get'), factory)
cli_command(__name__, 'documentdb list-keys', mgmt_path.format('DatabaseAccountsOperations.list_keys'), factory)
cli_command(__name__, 'documentdb list-read-only-keys', mgmt_path.format('DatabaseAccountsOperations.list_read_only_keys'), factory)
cli_command(__name__, 'documentdb regenerate-key', mgmt_path.format('DatabaseAccountsOperations.regenerate_key'), factory)
cli_command(__name__, 'documentdb check-name-exists', mgmt_path.format('DatabaseAccountsOperations.check_name_exists'), factory)
cli_command(__name__, 'documentdb delete', mgmt_path.format('DatabaseAccountsOperations.delete'), factory)
cli_command(__name__, 'documentdb failover-priority-change', mgmt_path.format('DatabaseAccountsOperations.failover_priority_change'), factory)
cli_command(__name__, 'documentdb create', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_create', cf_documentdb)
cli_command(__name__, 'documentdb update', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_update', cf_documentdb)
cli_command(__name__, 'documentdb list', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_list', cf_documentdb)
