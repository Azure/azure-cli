# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (get_mediaservices_client, get_transforms_client,
                              get_assets_client, get_jobs_client, get_streaming_locators_client,
                              get_streaming_policies_client, get_streaming_endpoints_client)
from ._exception_handler import ams_exception_handler


# pylint: disable=line-too-long

def load_command_table(self, _):  # pylint: disable=too-many-locals, too-many-statements
    def get_sdk(operation, client_factory):
        return CliCommandType(
            operations_tmpl='azure.mgmt.media.operations#{}Operations.'.format(operation) + '{}',
            client_factory=client_factory,
            exception_handler=ams_exception_handler
        )

    def get_custom_sdk(custom_module, client_factory):
        return CliCommandType(
            operations_tmpl='azure.cli.command_modules.ams.operations.{}#'.format(custom_module) + '{}',
            client_factory=client_factory,
            exception_handler=ams_exception_handler
        )

    with self.command_group('ams account', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.generic_update_command('update',
                                 getter_name='mediaservice_update_getter',
                                 getter_type=get_custom_sdk('account', get_mediaservices_client),
                                 custom_func_name='update_mediaservice',
                                 custom_func_type=get_custom_sdk('account', get_mediaservices_client))
        g.custom_command('list', 'list_mediaservices',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))
        g.custom_command('create', 'create_mediaservice',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))

    with self.command_group('ams account storage', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.custom_command('add', 'add_mediaservice_secondary_storage',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))
        g.custom_command('remove', 'remove_mediaservice_secondary_storage',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))

    with self.command_group('ams account sp', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.custom_command('create', 'create_assign_sp_to_mediaservice',
                         custom_command_type=get_custom_sdk('sp', get_mediaservices_client))
        g.custom_command('reset-credentials', 'reset_sp_credentials_for_mediaservice',
                         custom_command_type=get_custom_sdk('sp', get_mediaservices_client))

    with self.command_group('ams transform', get_sdk('Transforms', get_transforms_client)) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_transform',
                         custom_command_type=get_custom_sdk('transform', get_transforms_client))
        g.custom_command('update', 'update_transform',
                         custom_command_type=get_custom_sdk('transform', get_transforms_client))
        g.generic_update_command('update',
                                 setter_name='transform_update_setter',
                                 setter_type=get_custom_sdk('transform', get_mediaservices_client),
                                 custom_func_name='update_transform',
                                 custom_func_type=get_custom_sdk('transform', get_mediaservices_client))

    with self.command_group('ams transform output', get_sdk('Transforms', get_mediaservices_client)) as g:
        g.custom_command('add', 'add_transform_output',
                         custom_command_type=get_custom_sdk('transform', get_transforms_client))
        g.custom_command('remove', 'remove_transform_output',
                         custom_command_type=get_custom_sdk('transform', get_transforms_client))

    with self.command_group('ams asset', get_sdk('Assets', get_assets_client)) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.generic_update_command('update',
                                 custom_func_name='update_asset',
                                 custom_func_type=get_custom_sdk('asset', get_mediaservices_client))
        g.custom_command('get-sas-urls', 'get_sas_urls',
                         custom_command_type=get_custom_sdk('asset', get_assets_client))
        g.custom_command('create', 'create_asset',
                         custom_command_type=get_custom_sdk('asset', get_assets_client))

    with self.command_group('ams job', get_sdk('Jobs', get_jobs_client)) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('cancel', 'cancel_job',
                         custom_command_type=get_custom_sdk('job', get_jobs_client))
        g.custom_command('start', 'create_job',
                         custom_command_type=get_custom_sdk('job', get_jobs_client))

    with self.command_group('ams streaming locator', get_sdk('StreamingLocators', get_streaming_locators_client)) as g:
        g.custom_command('create', 'create_streaming_locator',
                         custom_command_type=get_custom_sdk('streaming', get_streaming_locators_client))
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.command('get-paths', 'list_paths')

    with self.command_group('ams streaming policy', get_sdk('StreamingPolicies', get_streaming_policies_client)) as g:
        g.custom_command('create', 'create_streaming_policy',
                         custom_command_type=get_custom_sdk('streaming', get_streaming_policies_client))
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.command('delete', 'delete')

    with self.command_group('ams streaming endpoint', get_sdk('StreamingEndpoints', get_streaming_endpoints_client)) as g:
        g.command('list', 'list')
        g.command('start', 'start')
        g.command('stop', 'stop')
