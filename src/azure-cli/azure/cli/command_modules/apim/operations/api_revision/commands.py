# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_api_revision


def load_command_table(commands_loader, _):
    sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#ApiRevisionOperations.{}',
        client_factory=cf_api_revision
    )

    custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.apim.operations.api_revision.custom#{}',
        client_factory=cf_api_revision
    )

    with commands_loader.command_group('apim api revision', sdk, custom_command_type=custom_type, client_factory=cf_api_revision, is_preview=True) as g:
        g.custom_command('list', 'list_api_revision')
        g.custom_command('create', 'create_api_revision')
