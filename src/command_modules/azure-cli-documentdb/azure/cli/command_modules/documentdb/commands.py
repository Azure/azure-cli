# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.documentdb._client_factory import (cf_documentdb)
from ._client_factory import get_document_client_factory
from ._command_type import cli_documentdb_data_plane_command

mgmt_path = 'azure.mgmt.documentdb.operations.database_accounts_operations#'
custome_path = 'azure.cli.command_modules.documentdb.custom#'


def db_accounts_factory(_):
    return cf_documentdb().database_accounts


cli_command(__name__, 'documentdb show', mgmt_path + 'DatabaseAccountsOperations.get', db_accounts_factory)
cli_command(__name__, 'documentdb list-keys', mgmt_path + 'DatabaseAccountsOperations.list_keys', db_accounts_factory)
cli_command(__name__, 'documentdb list-read-only-keys', mgmt_path + 'DatabaseAccountsOperations.list_read_only_keys', db_accounts_factory)
cli_command(__name__, 'documentdb list-connection-strings', mgmt_path + 'DatabaseAccountsOperations.list_connection_strings', db_accounts_factory)
cli_command(__name__, 'documentdb regenerate-key', mgmt_path + 'DatabaseAccountsOperations.regenerate_key', db_accounts_factory)
cli_command(__name__, 'documentdb check-name-exists', mgmt_path + 'DatabaseAccountsOperations.check_name_exists', db_accounts_factory)
cli_command(__name__, 'documentdb delete', mgmt_path + 'DatabaseAccountsOperations.delete', db_accounts_factory)
cli_command(__name__, 'documentdb failover-priority-change', mgmt_path + 'DatabaseAccountsOperations.failover_priority_change', db_accounts_factory)
cli_command(__name__, 'documentdb create', custome_path + 'cli_documentdb_create', db_accounts_factory)
cli_command(__name__, 'documentdb update', custome_path + 'cli_documentdb_update', db_accounts_factory)
cli_command(__name__, 'documentdb list', custome_path + 'cli_documentdb_list', db_accounts_factory)


# # database operations
cli_documentdb_data_plane_command('documentdb database show', custome_path + 'cli_documentdb_database_show', get_document_client_factory)
cli_documentdb_data_plane_command('documentdb database list', custome_path + 'cli_documentdb_database_list', get_document_client_factory)
cli_documentdb_data_plane_command('documentdb database exists', custome_path + 'cli_documentdb_database_exists', get_document_client_factory)
cli_documentdb_data_plane_command('documentdb database create', custome_path + 'cli_documentdb_database_create', get_document_client_factory)
cli_documentdb_data_plane_command('documentdb database delete', custome_path + 'cli_documentdb_database_delete', get_document_client_factory)

# collection operations
cli_documentdb_data_plane_command('documentdb collection show', custome_path + 'cli_documentdb_collection_show', get_document_client_factory)
cli_documentdb_data_plane_command('documentdb collection list', custome_path + 'cli_documentdb_collection_list', get_document_client_factory)
cli_documentdb_data_plane_command('documentdb collection exists', custome_path + 'cli_documentdb_collection_exists', get_document_client_factory)
cli_documentdb_data_plane_command('documentdb collection create', custome_path + 'cli_documentdb_collection_create', get_document_client_factory)
cli_documentdb_data_plane_command('documentdb collection delete', custome_path + 'cli_documentdb_collection_delete', get_document_client_factory)
cli_documentdb_data_plane_command('documentdb collection update', custome_path + 'cli_documentdb_collection_update', get_document_client_factory)
