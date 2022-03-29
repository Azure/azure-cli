# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from ._client_factory import (get_mediaservices_client, get_transforms_client,
                              get_assets_client, get_jobs_client, get_streaming_locators_client,
                              get_streaming_policies_client, get_streaming_endpoints_client,
                              get_locations_client, get_live_events_client, get_live_outputs_client,
                              get_content_key_policies_client, get_asset_filters_client,
                              get_account_filters_client)
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
        g.custom_show_command('show', 'get_mediaservice',
                              custom_command_type=get_custom_sdk('account', get_mediaservices_client))
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
        g.custom_command('check-name', 'check_name_availability',
                         custom_command_type=get_custom_sdk('account', get_locations_client))

    with self.command_group('ams account storage', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.custom_command('add', 'add_mediaservice_secondary_storage',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))
        g.custom_command('remove', 'remove_mediaservice_secondary_storage',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))
        g.custom_command('set-authentication', 'set_mediaservice_trusted_storage',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))
        g.custom_command('sync-storage-keys', 'sync_storage_keys',
                         custom_command_type=get_custom_sdk('account', get_mediaservices_client))

    with self.command_group('ams account sp', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.custom_command('create', 'create_or_update_assign_sp_to_mediaservice',
                         custom_command_type=get_custom_sdk('sp', get_mediaservices_client))
        g.custom_command('reset-credentials', 'reset_sp_credentials_for_mediaservice',
                         custom_command_type=get_custom_sdk('sp', get_mediaservices_client))

    with self.command_group('ams account mru', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.custom_show_command('show', 'get_mru',
                              custom_command_type=get_custom_sdk('mru', get_mediaservices_client))
        g.custom_command('set', 'set_mru',
                         custom_command_type=get_custom_sdk('mru', get_mediaservices_client))

    with self.command_group('ams account encryption', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.custom_show_command('show', 'get_encryption',
                              custom_command_type=get_custom_sdk('encryption', get_mediaservices_client))
        g.custom_command('set', 'set_encryption',
                         custom_command_type=get_custom_sdk('encryption', get_mediaservices_client))

    with self.command_group('ams account identity', get_sdk('Mediaservices', get_mediaservices_client)) as g:
        g.custom_show_command('assign', 'assign_identity',
                              custom_command_type=get_custom_sdk('identity', get_mediaservices_client))
        g.custom_command('remove', 'remove_identity',
                         custom_command_type=get_custom_sdk('identity', get_mediaservices_client))
        g.custom_show_command('show', 'show_identity',
                         custom_command_type=get_custom_sdk('identity', get_mediaservices_client))

    with self.command_group('ams transform', get_sdk('Transforms', get_transforms_client)) as g:
        g.custom_show_command('show', 'get_transform',
                              custom_command_type=get_custom_sdk('transform', get_transforms_client))
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_transform',
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
        g.custom_show_command('show', 'get_asset', custom_command_type=get_custom_sdk('asset', get_assets_client))
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.command('list-streaming-locators', 'list_streaming_locators')
        g.custom_command('get-encryption-key', 'get_encryption_key',
                         custom_command_type=get_custom_sdk('asset', get_assets_client))
        g.generic_update_command('update',
                                 custom_func_name='update_asset',
                                 custom_func_type=get_custom_sdk('asset', get_mediaservices_client))
        g.custom_command('get-sas-urls', 'get_sas_urls',
                         custom_command_type=get_custom_sdk('asset', get_assets_client))
        g.custom_command('create', 'create_asset',
                         custom_command_type=get_custom_sdk('asset', get_assets_client))

    with self.command_group('ams asset-filter', get_sdk('AssetFilters', get_asset_filters_client)) as g:
        g.command('list', 'list')
        g.custom_show_command('show', 'get_asset_filter',
                              custom_command_type=get_custom_sdk('asset_filter', get_asset_filters_client))
        g.command('delete', 'delete')
        g.custom_command('create', 'create_asset_filter',
                         custom_command_type=get_custom_sdk('asset_filter', get_asset_filters_client))
        g.generic_update_command('update',
                                 custom_func_name='update_asset_filter',
                                 custom_func_type=get_custom_sdk('asset_filter', get_mediaservices_client))

    with self.command_group('ams job', get_sdk('Jobs', get_jobs_client)) as g:
        g.custom_show_command('show', 'get_job',
                              custom_command_type=get_custom_sdk('job', get_jobs_client))
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.custom_command('cancel', 'cancel_job',
                         custom_command_type=get_custom_sdk('job', get_jobs_client))
        g.custom_command('start', 'create_job',
                         custom_command_type=get_custom_sdk('job', get_jobs_client))
        g.generic_update_command('update',
                                 setter_name='update',
                                 custom_func_name='update_job',
                                 custom_func_type=get_custom_sdk('job', get_jobs_client))

    with self.command_group('ams content-key-policy', get_sdk('ContentKeyPolicies', get_content_key_policies_client)) as g:
        g.custom_command('create', 'create_content_key_policy',
                         custom_command_type=get_custom_sdk('content_key_policy', get_content_key_policies_client))
        g.custom_show_command('show', 'show_content_key_policy',
                              custom_command_type=get_custom_sdk('content_key_policy', get_content_key_policies_client))
        g.command('delete', 'delete')
        g.command('list', 'list')
        g.generic_update_command('update',
                                 getter_name='get_policy_properties_with_secrets',
                                 setter_name='update_content_key_policy_setter',
                                 setter_type=get_custom_sdk('content_key_policy', get_content_key_policies_client),
                                 custom_func_name='update_content_key_policy',
                                 custom_func_type=get_custom_sdk('content_key_policy', get_content_key_policies_client))

    with self.command_group('ams content-key-policy option', get_sdk('ContentKeyPolicies', get_content_key_policies_client)) as g:
        g.custom_command('add', 'add_content_key_policy_option',
                         custom_command_type=get_custom_sdk('content_key_policy', get_content_key_policies_client))
        g.custom_command('remove', 'remove_content_key_policy_option',
                         custom_command_type=get_custom_sdk('content_key_policy', get_content_key_policies_client))
        g.custom_command('update', 'update_content_key_policy_option',
                         custom_command_type=get_custom_sdk('content_key_policy', get_content_key_policies_client))

    with self.command_group('ams streaming-locator', get_sdk('StreamingLocators', get_streaming_locators_client)) as g:
        g.custom_command('create', 'create_streaming_locator',
                         custom_command_type=get_custom_sdk('streaming_locator', get_streaming_locators_client))
        g.command('list', 'list')
        g.custom_show_command('show', 'get_streaming_locator',
                              custom_command_type=get_custom_sdk('streaming_locator', get_streaming_locators_client))
        g.command('delete', 'delete')
        g.command('get-paths', 'list_paths')
        g.custom_command('list-content-keys', 'list_content_keys',
                         custom_command_type=get_custom_sdk('streaming_locator', get_streaming_locators_client))

    with self.command_group('ams streaming-policy', get_sdk('StreamingPolicies', get_streaming_policies_client)) as g:
        g.custom_command('create', 'create_streaming_policy',
                         custom_command_type=get_custom_sdk('streaming_policy', get_streaming_policies_client))
        g.command('list', 'list')
        g.custom_show_command('show', 'get_streaming_policy',
                              custom_command_type=get_custom_sdk('streaming_policy', get_streaming_policies_client))
        g.command('delete', 'delete')

    with self.command_group('ams streaming-endpoint', get_sdk('StreamingEndpoints', get_streaming_endpoints_client)) as g:
        g.command('list', 'list')
        g.custom_command('start', 'start',
                         custom_command_type=get_custom_sdk('streaming_endpoint', get_streaming_endpoints_client),
                         supports_no_wait=True)
        g.custom_command('stop', 'stop',
                         custom_command_type=get_custom_sdk('streaming_endpoint', get_streaming_endpoints_client),
                         supports_no_wait=True)
        g.custom_command('create', 'create_streaming_endpoint',
                         custom_command_type=get_custom_sdk('streaming_endpoint', get_streaming_endpoints_client),
                         supports_no_wait=True)
        g.custom_command('scale', 'scale',
                         custom_command_type=get_custom_sdk('streaming_endpoint', get_streaming_endpoints_client))
        g.generic_update_command('update',
                                 setter_name='update_streaming_endpoint_setter',
                                 setter_type=get_custom_sdk('streaming_endpoint', get_streaming_endpoints_client),
                                 custom_func_name='update_streaming_endpoint',
                                 custom_func_type=get_custom_sdk('streaming_endpoint', get_streaming_endpoints_client),
                                 supports_no_wait=True)
        g.custom_show_command('show', 'get_streaming_endpoint',
                              custom_command_type=get_custom_sdk('streaming_endpoint', get_streaming_endpoints_client))
        g.command('delete', 'begin_delete')
        g.wait_command('wait')

    with self.command_group('ams streaming-endpoint akamai', get_sdk('StreamingEndpoints', get_streaming_endpoints_client)) as g:
        g.custom_command('add', 'add_akamai_access_control',
                         custom_command_type=get_custom_sdk('streaming_endpoint', get_streaming_endpoints_client))
        g.custom_command('remove', 'remove_akamai_access_control',
                         custom_command_type=get_custom_sdk('streaming_endpoint', get_streaming_endpoints_client))

    with self.command_group('ams live-event', get_sdk('LiveEvents', get_live_events_client)) as g:
        g.custom_command('create', 'create',
                         custom_command_type=get_custom_sdk('live_event', get_live_events_client),
                         supports_no_wait=True)
        g.custom_command('start', 'start',
                         custom_command_type=get_custom_sdk('live_event', get_live_events_client),
                         supports_no_wait=True)
        g.custom_command('standby', 'standby',
                         custom_command_type=get_custom_sdk('live_event', get_live_events_client),
                         supports_no_wait=True)
        g.custom_command('stop', 'stop',
                         custom_command_type=get_custom_sdk('live_event', get_live_events_client),
                         supports_no_wait=True)
        g.custom_command('reset', 'reset',
                         custom_command_type=get_custom_sdk('live_event', get_live_events_client),
                         supports_no_wait=True)
        g.custom_show_command('show', 'get_live_event',
                              custom_command_type=get_custom_sdk('live_event', get_live_events_client))
        g.command('delete', 'begin_delete')
        g.command('list', 'list')
        g.generic_update_command('update',
                                 setter_name='update_live_event_setter',
                                 setter_type=get_custom_sdk('live_event', get_live_events_client),
                                 custom_func_name='update_live_event',
                                 custom_func_type=get_custom_sdk('live_event', get_live_events_client))
        g.wait_command('wait')

    with self.command_group('ams live-output', get_sdk('LiveOutputs', get_live_outputs_client)) as g:
        g.custom_command('create', 'create_live_output',
                         custom_command_type=get_custom_sdk('live_output', get_live_outputs_client))
        g.custom_show_command('show', 'get_live_output',
                              custom_command_type=get_custom_sdk('live_output', get_live_outputs_client))
        g.command('list', 'list')
        g.command('delete', 'begin_delete')

    with self.command_group('ams account-filter', get_sdk('AccountFilters', get_account_filters_client)) as g:
        g.custom_command('create', 'create_account_filter',
                         custom_command_type=get_custom_sdk('account_filter', get_account_filters_client))
        g.custom_show_command('show', 'get_account_filter',
                              custom_command_type=get_custom_sdk('account_filter', get_account_filters_client))
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.generic_update_command('update',
                                 custom_func_name='update_account_filter',
                                 custom_func_type=get_custom_sdk('account_filter', get_mediaservices_client))

    with self.command_group('ams'):
        pass
