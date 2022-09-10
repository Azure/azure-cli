# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.apim._client_factory import cf_deleted_services


def load_command_table(commands_loader, _):
    deleted_service_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.apimanagement.operations#DeletedServicesOperations.{}',
        client_factory=cf_deleted_services
    )

    deleted_service_custom_type = CliCommandType(
        operations_tmpl='azure.cli.command_modules.apim.operations.deleted_service.custom#{}',
        client_factory=cf_deleted_services
    )

    with commands_loader.command_group('apim deleted-service', deleted_service_sdk, custom_command_type=deleted_service_custom_type,
                                       is_preview=True, client_factory=cf_deleted_services) as g:
        g.custom_command('list', 'list_deleted_service')
        g.custom_show_command('show', 'get_deleted_service')
        g.custom_command('purge', 'purge_deleted_service', supports_no_wait=True)
