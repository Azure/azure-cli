# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import cli_command

from azure.cli.command_modules.cognitiveservices._client_factory import cognitiveservices_client_factory

mgmt_path = 'azure.mgmt.cognitiveservices.operations.cognitive_services_accounts_operations#CognitiveServicesAccountsOperations.'
custom_path = 'azure.cli.command_modules.cognitiveservices.custom#'

cli_command(__name__, 'cognitiveservices account create', custom_path + 'create', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account delete', mgmt_path + 'delete', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account show',  mgmt_path + 'get_properties', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account list',  custom_path + 'list', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account update', mgmt_path + 'update', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account keys regenerate', mgmt_path + 'regenerate_key', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account keys list', mgmt_path + 'list_keys', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices account list-skus', mgmt_path + 'list_skus', cognitiveservices_client_factory)
cli_command(__name__, 'cognitiveservices list-skus', mgmt_path + 'list_skus', cognitiveservices_client_factory)


