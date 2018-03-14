# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (cf_media, get_mediaservices_client, get_transforms_client, get_assets_client)
from ._exception_handler import (build_exception_wrapper)


def load_command_table(self, _):
    ams_sdk = CliCommandType(
        operations_tmpl='azure.mediav3.operations#MediaservicesOperations.{}',
        client_factory=cf_media,
        exception_handler=build_exception_wrapper()
    )

    ams_encoding_sdk = CliCommandType(
        operations_tmpl='azure.mediav3.operations#TransformsOperations.{}',
        client_factory=cf_media,
        exception_handler=build_exception_wrapper()
    )

    ams_asset_sdk = CliCommandType(
        operations_tmpl='azure.mediav3.operations#AssetsOperations.{}',
        client_factory=cf_media,
        exception_handler=build_exception_wrapper()
    )

    ams_account_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.ams.operations.account#{}',
        exception_handler=build_exception_wrapper()
    )

    ams_sp_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.ams.operations.sp#{}',
        exception_handler=build_exception_wrapper()
    )

    ams_transform_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.ams.operations.transform#{}',
        exception_handler=build_exception_wrapper()
    )

    ams_asset_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.ams.operations.asset#{}',
        exception_handler=build_exception_wrapper()
    )

    with self.command_group('ams account', ams_sdk) as g:
        g.command('show', 'get')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_mediaservices', custom_command_type=ams_account_custom,
                         client_factory=get_mediaservices_client)
        g.custom_command('create', 'create_mediaservice', custom_command_type=ams_account_custom,
                         client_factory=get_mediaservices_client)

    with self.command_group('ams storage', ams_sdk) as g:
        g.custom_command('add', 'add_mediaservice_secondary_storage', custom_command_type=ams_account_custom,
                         client_factory=get_mediaservices_client)
        g.custom_command('remove', 'remove_mediaservice_secondary_storage', custom_command_type=ams_account_custom,
                         client_factory=get_mediaservices_client)

    with self.command_group('ams sp', ams_sdk) as g:
        g.custom_command('create', 'create_assign_sp_to_mediaservice', custom_command_type=ams_sp_custom,
                         client_factory=get_mediaservices_client)

    with self.command_group('ams transform', ams_encoding_sdk) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_transform', custom_command_type=ams_transform_custom,
                         client_factory=get_transforms_client)
        g.custom_command('update', 'update_transform', custom_command_type=ams_transform_custom,
                         client_factory=get_transforms_client)

    with self.command_group('ams transform output', ams_encoding_sdk) as g:
        g.custom_command('add', 'add_transform_output', custom_command_type=ams_transform_custom,
                         client_factory=get_transforms_client)
        g.custom_command('remove', 'remove_transform_output', custom_command_type=ams_transform_custom,
                         client_factory=get_transforms_client)

    with self.command_group('ams asset', ams_asset_sdk) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_asset', custom_command_type=ams_asset_custom,
                         client_factory=get_assets_client)
