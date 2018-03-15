# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (get_mediaservices_client, get_transforms_client,
                              get_assets_client, get_jobs_client)
from ._exception_handler import (build_exception_wrapper)


def load_command_table(self, _):  # pylint: disable=too-many-locals, too-many-statements
    def get_sdk(operation, client_factory):
        return CliCommandType(
            operations_tmpl='azure.mediav3.operations#{}Operations.'.format(operation) + '{}',
            client_factory=client_factory,
            exception_handler=build_exception_wrapper()
        )

    def get_custom_sdk(custom_module, client_factory):
        return CliCommandType(
            operations_tmpl='azure.cli.command_modules.ams.operations.{}#'.format(custom_module) + '{}',
            client_factory=client_factory,
            exception_handler=build_exception_wrapper()
        )

    with self.command_group('ams account', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.command('show', 'get')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_mediaservices',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))
        g.custom_command('create', 'create_mediaservice',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))

    with self.command_group('ams storage', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.custom_command('add', 'add_mediaservice_secondary_storage',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))
        g.custom_command('remove', 'remove_mediaservice_secondary_storage',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))

    with self.command_group('ams sp', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.custom_command('create', 'create_assign_sp_to_mediaservice',
                         custom_command_type=get_custom_sdk('sp', get_mediaservices_client))

    with self.command_group('ams transform', get_sdk('Transforms', get_transforms_client)) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_transform',
                         custom_command_type=get_custom_sdk('transform', get_transforms_client))
        g.custom_command('update', 'update_transform',
                         custom_command_type=get_custom_sdk('transform', get_transforms_client))

    with self.command_group('ams transform output', get_sdk('Transforms', get_mediaservices_client)) as g:
        g.custom_command('add', 'add_transform_output',
                         custom_command_type=get_custom_sdk('transform', get_transforms_client))
        g.custom_command('remove', 'remove_transform_output',
                         custom_command_type=get_custom_sdk('transform', get_transforms_client))

    with self.command_group('ams asset', get_sdk('Assets', get_assets_client)) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_asset',
                         custom_command_type=get_custom_sdk('asset', get_assets_client))

    with self.command_group('ams job', get_sdk('Jobs', get_jobs_client)) as g:
        g.command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.command('cancel', 'cancel_job')
        g.custom_command('create', 'create_job',
                         custom_command_type=get_custom_sdk('job', get_jobs_client))
