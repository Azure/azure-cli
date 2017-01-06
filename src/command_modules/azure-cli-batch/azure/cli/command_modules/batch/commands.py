# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command

from ._client_factory import batch_client_factory

data_path = 'azure.batch.operations.{}_operations#{}'
custom_path = 'azure.cli.command_modules.batch.custom#{}'
mgmt_path = 'azure.mgmt.batch.operations.{}_operations#{}'

# pylint: disable=line-too-long
# Mgmt Account Operations

factory = lambda args: batch_client_factory(**args).batch_account
cli_command(__name__, 'batch account list', custom_path.format('list_accounts'), factory)
cli_command(__name__, 'batch account show', mgmt_path.format('batch_account', 'BatchAccountOperations.get'), factory)
cli_command(__name__, 'batch account create', custom_path.format('create_account'), factory)
cli_command(__name__, 'batch account set', custom_path.format('update_account'), factory)
cli_command(__name__, 'batch account delete', mgmt_path.format('batch_account', 'BatchAccountOperations.delete'), factory)
cli_command(__name__, 'batch account autostorage-keys sync', mgmt_path.format('batch_account', 'BatchAccountOperations.synchronize_auto_storage_keys'), factory)

cli_command(__name__, 'batch account keys list', mgmt_path.format('batch_account', 'BatchAccountOperations.get_keys'), factory)
cli_command(__name__, 'batch account keys renew', mgmt_path.format('batch_account', 'BatchAccountOperations.regenerate_key'), factory)


factory = lambda args: batch_client_factory(**args).application
cli_command(__name__, 'batch application list', mgmt_path.format('application', 'ApplicationOperations.list'), factory)
cli_command(__name__, 'batch application show', mgmt_path.format('application', 'ApplicationOperations.get'), factory)
cli_command(__name__, 'batch application create', mgmt_path.format('application', 'ApplicationOperations.create'), factory)
cli_command(__name__, 'batch application set', custom_path.format('update_application'), factory)
cli_command(__name__, 'batch application delete', mgmt_path.format('application', 'ApplicationOperations.delete'), factory)


factory = lambda args: batch_client_factory(**args).application_package
cli_command(__name__, 'batch application package create', custom_path.format('create_application_package'), factory)
cli_command(__name__, 'batch application package delete', mgmt_path.format('application_package', 'ApplicationPackageOperations.delete'), factory)
cli_command(__name__, 'batch application package show', mgmt_path.format('application_package', 'ApplicationPackageOperations.get'), factory)
cli_command(__name__, 'batch application package activate', mgmt_path.format('application_package', 'ApplicationPackageOperations.activate'), factory)


factory = lambda args: batch_client_factory(**args).location
cli_command(__name__, 'batch location quotas show', mgmt_path.format('location', 'LocationOperations.get_quotas'), factory)
