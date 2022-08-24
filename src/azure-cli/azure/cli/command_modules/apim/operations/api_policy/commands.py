# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_api_policy
from azure.cli.command_modules.apim._format import api_policy_output_format
from .validators import validate_policy_xml_content


def load_command_table(commands_loader, _):
    api_policy_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiPolicyOperations.{}',
        client_factory=cf_api_policy
    )

    api_policy_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.apim.operations.api_policy.custom#{}',
        client_factory=cf_api_policy
    )

    with commands_loader.command_group('apim api policy', api_policy_sdk, custom_command_type=api_policy_custom_type, is_preview=True, client_factory=cf_api_policy) as g:
        g.custom_command('create', 'create_api_policy', supports_no_wait=True, table_transformer=api_policy_output_format, validator=validate_policy_xml_content)
        g.custom_command('update', 'update_api_policy', supports_no_wait=True, table_transformer=api_policy_output_format, validator=validate_policy_xml_content)
        g.custom_command('list', 'list_api_policy', table_transformer=api_policy_output_format)
        g.custom_show_command('show', 'show_api_policy', table_transformer=None)
        g.custom_command('delete', 'delete_api_policy', table_transformer=api_policy_output_format)
