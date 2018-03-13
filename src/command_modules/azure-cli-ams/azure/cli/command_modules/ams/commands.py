# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (cf_media, get_mediaservices_client, get_transforms_client)
from ._exception_handler import (ams_resource_not_found, storage_account_not_found)


def load_command_table(self, _):
    ams_sdk = CliCommandType(
        operations_tmpl='azure.mediav3.operations#MediaservicesOperations.{}',
        client_factory=cf_media,
        exception_handler=ams_resource_not_found('Media Service')
    )

    ams_encoding_sdk = CliCommandType(
        operations_tmpl='azure.mediav3.operations#TransformsOperations.{}',
        client_factory=cf_media,
        exception_handler=ams_resource_not_found('Media Service')
    )

    ams_account_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.ams.operations.account#{}'
    )

    ams_sp_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.ams.operations.sp#{}'
    )

    ams_transform_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.ams.operations.transform#{}'
    )

    with self.command_group('ams account', ams_sdk) as g:
        g.command('show', 'get')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_mediaservices', custom_command_type=ams_account_custom,
                         client_factory=get_mediaservices_client)
        g.custom_command('create', 'create_mediaservice', custom_command_type=ams_account_custom,
                         client_factory=get_mediaservices_client,
                         exception_handler=storage_account_not_found())

    with self.command_group('ams storage', ams_sdk) as g:
        g.custom_command('add', 'add_mediaservice_secondary_storage', custom_command_type=ams_account_custom,
                         client_factory=get_mediaservices_client,
                         exception_handler=storage_account_not_found())
        g.custom_command('remove', 'remove_mediaservice_secondary_storage', custom_command_type=ams_account_custom,
                         client_factory=get_mediaservices_client)

    with self.command_group('ams sp', ams_sdk) as g:
        g.custom_command('create', 'create_assign_sp_to_mediaservice', custom_command_type=ams_sp_custom,
                         client_factory=get_mediaservices_client,
                         exception_handler=ams_resource_not_found('Media Service'))

    with self.command_group('ams transform', ams_encoding_sdk) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.custom_command('create', 'create_transform', custom_command_type=ams_transform_custom,
                         client_factory=get_transforms_client)
