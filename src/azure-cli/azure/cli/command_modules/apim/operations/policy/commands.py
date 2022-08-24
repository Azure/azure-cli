# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_policy
from azure.cli.command_modules.apim._format import policy_output_format
from .validators import validate_policy_xml_content


def load_command_table(commands_loader, _):
    policy_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#PolicyOperations.{}',
        client_factory=cf_policy
    )

    policy_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.apim.operations.policy.custom#{}',
        client_factory=cf_policy
    )

    with commands_loader.command_group('apim policy', policy_sdk, custom_command_type=policy_custom_type, client_factory=cf_policy, is_preview=True) as g:
        g.custom_command('create', 'create_policy', supports_no_wait=True, table_transformer=policy_output_format, validator=validate_policy_xml_content)
        g.custom_show_command('show', 'get_policy', table_transformer=policy_output_format)
        g.custom_command('delete', 'delete_policy', confirmation=True, supports_no_wait=True)
        g.custom_command('update', 'update_policy', table_transformer=policy_output_format, validator=validate_policy_xml_content)
