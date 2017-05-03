# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import cli_command
from azure.cli.command_modules.cognitiveservices._client_factory import (
    get_cognitiveservices_account_operations,
    get_cognitiveservices_operations)

mgmt_path = 'azure.mgmt.cognitiveservices.operations.cognitive_services_accounts_operations#'\
    'CognitiveServicesAccountsOperations.{}'
custom_path = 'azure.cli.command_modules.cognitiveservices.custom#{}'

cli_command(__name__, 'cognitiveservices account create', custom_path.format('create'),
            get_cognitiveservices_account_operations)
cli_command(__name__, 'cognitiveservices account delete', mgmt_path.format('delete'),
            get_cognitiveservices_account_operations)
cli_command(__name__, 'cognitiveservices account show', mgmt_path.format('get_properties'),
            get_cognitiveservices_account_operations)
cli_command(__name__, 'cognitiveservices list', custom_path.format('listresources'),
            get_cognitiveservices_operations)
cli_command(__name__, 'cognitiveservices account update', custom_path.format('update'),
            get_cognitiveservices_account_operations)
cli_command(__name__, 'cognitiveservices account keys regenerate',
            mgmt_path.format('regenerate_key'),
            get_cognitiveservices_account_operations)
cli_command(__name__, 'cognitiveservices account keys list', mgmt_path.format('list_keys'),
            get_cognitiveservices_account_operations)
cli_command(__name__, 'cognitiveservices account list-skus', mgmt_path.format('list_skus'),
            get_cognitiveservices_account_operations)
