# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.application import APPLICATION
from azure.cli.core.commands import cli_command
from azure.cli.command_modules.cosmosdb._client_factory import (cf_documentdb)
from ._client_factory import get_document_client_factory
from ._command_type import cli_cosmosdb_data_plane_command

mgmt_path = 'azure.mgmt.documentdb.operations.database_accounts_operations#'
custome_path = 'azure.cli.command_modules.cosmosdb.custom#'


def deprecate(argv):
    if argv[0] == 'documentdb':
        from azure.cli.core.util import CLIError
        raise CLIError('All documentdb commands have been renamed to cosmosdb')


APPLICATION.register(APPLICATION.COMMAND_PARSER_PARSING, deprecate)


def db_accounts_factory(_):
    return cf_documentdb().database_accounts


cli_command(__name__, 'cosmosdb show', mgmt_path + 'DatabaseAccountsOperations.get', db_accounts_factory)
cli_command(__name__, 'cosmosdb list-keys', mgmt_path + 'DatabaseAccountsOperations.list_keys', db_accounts_factory)
cli_command(__name__, 'cosmosdb list-read-only-keys', mgmt_path + 'DatabaseAccountsOperations.list_read_only_keys', db_accounts_factory)
cli_command(__name__, 'cosmosdb list-connection-strings', mgmt_path + 'DatabaseAccountsOperations.list_connection_strings', db_accounts_factory)
cli_command(__name__, 'cosmosdb regenerate-key', mgmt_path + 'DatabaseAccountsOperations.regenerate_key', db_accounts_factory)
cli_command(__name__, 'cosmosdb check-name-exists', mgmt_path + 'DatabaseAccountsOperations.check_name_exists', db_accounts_factory)
cli_command(__name__, 'cosmosdb delete', mgmt_path + 'DatabaseAccountsOperations.delete', db_accounts_factory)
cli_command(__name__, 'cosmosdb failover-priority-change', mgmt_path + 'DatabaseAccountsOperations.failover_priority_change', db_accounts_factory)
cli_command(__name__, 'cosmosdb create', custome_path + 'cli_cosmosdb_create', db_accounts_factory)
cli_command(__name__, 'cosmosdb update', custome_path + 'cli_cosmosdb_update', db_accounts_factory)
cli_command(__name__, 'cosmosdb list', custome_path + 'cli_cosmosdb_list', db_accounts_factory)


# # database operations
cli_cosmosdb_data_plane_command('cosmosdb database show', custome_path + 'cli_cosmosdb_database_show', get_document_client_factory)
cli_cosmosdb_data_plane_command('cosmosdb database list', custome_path + 'cli_cosmosdb_database_list', get_document_client_factory)
cli_cosmosdb_data_plane_command('cosmosdb database exists', custome_path + 'cli_cosmosdb_database_exists', get_document_client_factory)
cli_cosmosdb_data_plane_command('cosmosdb database create', custome_path + 'cli_cosmosdb_database_create', get_document_client_factory)
cli_cosmosdb_data_plane_command('cosmosdb database delete', custome_path + 'cli_cosmosdb_database_delete', get_document_client_factory)

# collection operations
cli_cosmosdb_data_plane_command('cosmosdb collection show', custome_path + 'cli_cosmosdb_collection_show', get_document_client_factory)
cli_cosmosdb_data_plane_command('cosmosdb collection list', custome_path + 'cli_cosmosdb_collection_list', get_document_client_factory)
cli_cosmosdb_data_plane_command('cosmosdb collection exists', custome_path + 'cli_cosmosdb_collection_exists', get_document_client_factory)
cli_cosmosdb_data_plane_command('cosmosdb collection create', custome_path + 'cli_cosmosdb_collection_create', get_document_client_factory)
cli_cosmosdb_data_plane_command('cosmosdb collection delete', custome_path + 'cli_cosmosdb_collection_delete', get_document_client_factory)
cli_cosmosdb_data_plane_command('cosmosdb collection update', custome_path + 'cli_cosmosdb_collection_update', get_document_client_factory)
