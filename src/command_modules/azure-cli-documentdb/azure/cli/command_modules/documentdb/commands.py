# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
import azure.cli.command_modules.documentdb
# from azure.cli.command_modules.documentdb._client_factory import (cf_documentdb, cf_patch_schedules)

cli_command(__name__, 'documentdb create', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_create', cf_documentdb)
# cli_command(__name__, 'documentdb delete', 'azure.mgmt.documentdb.operations.documentdb_operations#documentdbOperations.delete', cf_documentdb)
# cli_command(__name__, 'documentdb export', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_export', cf_documentdb)
# cli_command(__name__, 'documentdb force-reboot', 'azure.mgmt.documentdb.operations.documentdb_operations#documentdbOperations.force_reboot', cf_documentdb)
# cli_command(__name__, 'documentdb import-method', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_import_method', cf_documentdb)
# cli_command(__name__, 'documentdb list', 'azure.mgmt.documentdb.operations.documentdb_operations#documentdbOperations.list_by_resource_group', cf_documentdb)
# cli_command(__name__, 'documentdb list-all', 'azure.mgmt.documentdb.operations.documentdb_operations#documentdbOperations.list', cf_documentdb)
# cli_command(__name__, 'documentdb list-keys', 'azure.mgmt.documentdb.operations.documentdb_operations#documentdbOperations.list_keys', cf_documentdb)
# cli_command(__name__, 'documentdb regenerate-keys', 'azure.mgmt.documentdb.operations.documentdb_operations#documentdbOperations.regenerate_key', cf_documentdb)
cli_command(__name__, 'documentdb show', 'azure.mgmt.documentdb.operations.documentdb_operations#documentdbOperations.get', cf_documentdb)
# cli_command(__name__, 'documentdb update-settings', 'azure.cli.command_modules.documentdb.custom#cli_documentdb_update_settings', cf_documentdb)

# cli_command(__name__, 'documentdb patch-schedule set', 'azure.mgmt.documentdb.operations.patch_schedules_operations#PatchSchedulesOperations.create_or_update', cf_patch_schedules)
# cli_command(__name__, 'documentdb patch-schedule delete', 'azure.mgmt.documentdb.operations.patch_schedules_operations#PatchSchedulesOperations.delete', cf_patch_schedules)
# cli_command(__name__, 'documentdb patch-schedule show', 'azure.mgmt.documentdb.operations.patch_schedules_operations#PatchSchedulesOperations.get', cf_patch_schedules)

