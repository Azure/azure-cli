# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.profiles import ResourceType
from azure.cli.core.sdk.util import CliCommandType
from azure.cli.core.util import empty_on_404

#from azure.cli.command_modules.storage._command_type import cli_storage_data_plane_command
from azure.cli.command_modules.storage.sdkutil import cosmosdb_table_exists
from azure.cli.command_modules.storage._client_factory import \
    (cf_sa, storage_client_factory, blob_data_service_factory, file_data_service_factory,
     table_data_service_factory, queue_data_service_factory, cloud_storage_account_service_factory,
     page_blob_service_factory, multi_service_properties_factory)
from azure.cli.command_modules.storage._format import \
    (transform_container_list, transform_container_show,
     transform_blob_output,
     transform_share_list,
     transform_file_output,
     transform_entity_show,
     transform_message_show,
     transform_boolean_for_table,
     transform_file_directory_result)
from azure.cli.command_modules.storage._transformers import \
    (transform_acl_list_output, transform_cors_list_output, transform_entity_query_output,
     transform_logging_list_output, transform_metrics_list_output,
     transform_url, transform_storage_list_output, transform_container_permission_output,
     create_boolean_result_output_transformer)

#custom_path = 'azure.cli.command_modules.storage.custom#'
#file_service_path = 'azure.multiapi.storage.file.fileservice#FileService.'
#block_blob_path = 'azure.multiapi.storage.blob.blockblobservice#BlockBlobService.'
#page_blob_path = 'azure.multiapi.storage.blob.pageblobservice#PageBlobService.'
#base_blob_path = 'azure.multiapi.storage.blob.baseblobservice#BaseBlobService.'
#queue_path = 'azure.multiapi.storage.queue.queueservice#QueueService.'

#if cosmosdb_table_exists():
#    table_path = 'azure.multiapi.cosmosdb.table.tableservice#TableService.'
#else:
#    table_path = 'azure.multiapi.storage.table.tableservice#TableService.'


#def _dont_fail_not_exist(ex):
#    AzureMissingResourceHttpError = get_sdk(ResourceType.DATA_STORAGE, 'common._error#AzureMissingResourceHttpError')
#    if isinstance(ex, AzureMissingResourceHttpError):
#        return None
#    else:
#        raise ex

## container commands
#factory = blob_data_service_factory
#cli_storage_data_plane_command('storage container list', block_blob_path + 'list_containers', factory, transform=transform_storage_list_output, table_transformer=transform_container_list)
#cli_storage_data_plane_command('storage container delete', block_blob_path + 'delete_container', factory, transform=create_boolean_result_output_transformer('deleted'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage container show', block_blob_path + 'get_container_properties', factory, table_transformer=transform_container_show, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage container create', block_blob_path + 'create_container', factory, transform=create_boolean_result_output_transformer('created'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage container generate-sas', block_blob_path + 'generate_container_shared_access_signature', factory)
#cli_storage_data_plane_command('storage container metadata update', block_blob_path + 'set_container_metadata', factory)
#cli_storage_data_plane_command('storage container metadata show', block_blob_path + 'get_container_metadata', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage container lease acquire', block_blob_path + 'acquire_container_lease', factory)
#cli_storage_data_plane_command('storage container lease renew', block_blob_path + 'renew_container_lease', factory)
#cli_storage_data_plane_command('storage container lease release', block_blob_path + 'release_container_lease', factory)
#cli_storage_data_plane_command('storage container lease change', block_blob_path + 'change_container_lease', factory)
#cli_storage_data_plane_command('storage container lease break', block_blob_path + 'break_container_lease', factory)
#cli_storage_data_plane_command('storage container exists', base_blob_path + 'exists', factory, transform=create_boolean_result_output_transformer('exists'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage container set-permission', base_blob_path + 'set_container_acl', factory)
#cli_storage_data_plane_command('storage container show-permission', base_blob_path + 'get_container_acl', factory, transform=transform_container_permission_output)
#cli_storage_data_plane_command('storage container policy create', custom_path + 'create_acl_policy', factory)
#cli_storage_data_plane_command('storage container policy delete', custom_path + 'delete_acl_policy', factory)
#cli_storage_data_plane_command('storage container policy show', custom_path + 'get_acl_policy', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage container policy list', custom_path + 'list_acl_policies', factory, table_transformer=transform_acl_list_output)
#cli_storage_data_plane_command('storage container policy update', custom_path + 'set_acl_policy', factory,
#                               resource_type=ResourceType.DATA_STORAGE, min_api='2017-04-17')

## blob commands
#cli_storage_data_plane_command('storage blob list', block_blob_path + 'list_blobs', factory, transform=transform_storage_list_output, table_transformer=transform_blob_output)
#cli_storage_data_plane_command('storage blob delete', block_blob_path + 'delete_blob', factory, transform=create_boolean_result_output_transformer('deleted'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage blob generate-sas', block_blob_path + 'generate_blob_shared_access_signature', factory)
#cli_storage_data_plane_command('storage blob url', block_blob_path + 'make_blob_url', factory, transform=transform_url)
#cli_storage_data_plane_command('storage blob snapshot', block_blob_path + 'snapshot_blob', factory)
#cli_storage_data_plane_command('storage blob show', block_blob_path + 'get_blob_properties', factory, table_transformer=transform_blob_output, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage blob update', block_blob_path + 'set_blob_properties', factory)
#cli_storage_data_plane_command('storage blob exists', base_blob_path + 'exists', factory, transform=create_boolean_result_output_transformer('exists'))
#cli_storage_data_plane_command('storage blob download', base_blob_path + 'get_blob_to_path', factory)
#cli_storage_data_plane_command('storage blob upload', 'azure.cli.command_modules.storage.blob#upload_blob', factory)
#cli_storage_data_plane_command('storage blob metadata show', block_blob_path + 'get_blob_metadata', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage blob metadata update', block_blob_path + 'set_blob_metadata', factory)
#cli_storage_data_plane_command('storage blob service-properties show', base_blob_path + 'get_blob_service_properties', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage blob lease acquire', block_blob_path + 'acquire_blob_lease', factory)
#cli_storage_data_plane_command('storage blob lease renew', block_blob_path + 'renew_blob_lease', factory)
#cli_storage_data_plane_command('storage blob lease release', block_blob_path + 'release_blob_lease', factory)
#cli_storage_data_plane_command('storage blob lease change', block_blob_path + 'change_blob_lease', factory)
#cli_storage_data_plane_command('storage blob lease break', block_blob_path + 'break_blob_lease', factory)
#cli_storage_data_plane_command('storage blob copy start', block_blob_path + 'copy_blob', factory)
#cli_storage_data_plane_command('storage blob copy start-batch', 'azure.cli.command_modules.storage.blob#storage_blob_copy_batch', factory)
#cli_storage_data_plane_command('storage blob copy cancel', block_blob_path + 'abort_copy_blob', factory)
#cli_storage_data_plane_command('storage blob upload-batch', 'azure.cli.command_modules.storage.blob#storage_blob_upload_batch', factory)
#cli_storage_data_plane_command('storage blob download-batch', 'azure.cli.command_modules.storage.blob#storage_blob_download_batch', factory)
#cli_storage_data_plane_command('storage blob delete-batch', 'azure.cli.command_modules.storage.blob#storage_blob_delete_batch', factory)
#cli_storage_data_plane_command('storage blob set-tier', custom_path + 'set_blob_tier', factory)

## page blob commands
#cli_storage_data_plane_command('storage blob incremental-copy start',
#                               page_blob_path + 'incremental_copy_blob', page_blob_service_factory)
#cli_storage_data_plane_command('storage blob incremental-copy cancel',
#                               block_blob_path + 'abort_copy_blob', page_blob_service_factory)

## share commands
#factory = file_data_service_factory
#cli_storage_data_plane_command('storage share list', file_service_path + 'list_shares', factory, transform=transform_storage_list_output, table_transformer=transform_share_list)
#cli_storage_data_plane_command('storage share create', file_service_path + 'create_share', factory, transform=create_boolean_result_output_transformer('created'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage share delete', file_service_path + 'delete_share', factory, transform=create_boolean_result_output_transformer('deleted'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage share generate-sas', file_service_path + 'generate_share_shared_access_signature', factory)
#cli_storage_data_plane_command('storage share stats', file_service_path + 'get_share_stats', factory)
#cli_storage_data_plane_command('storage share show', file_service_path + 'get_share_properties', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage share update', file_service_path + 'set_share_properties', factory)
#cli_storage_data_plane_command('storage share metadata show', file_service_path + 'get_share_metadata', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage share metadata update', file_service_path + 'set_share_metadata', factory)
#cli_storage_data_plane_command('storage share exists', file_service_path + 'exists', factory, transform=create_boolean_result_output_transformer('exists'))
#cli_storage_data_plane_command('storage share policy create', custom_path + 'create_acl_policy', factory)
#cli_storage_data_plane_command('storage share policy delete', custom_path + 'delete_acl_policy', factory)
#cli_storage_data_plane_command('storage share policy show', custom_path + 'get_acl_policy', factory)
#cli_storage_data_plane_command('storage share policy list', custom_path + 'list_acl_policies', factory, table_transformer=transform_acl_list_output)
#cli_storage_data_plane_command('storage share policy update', custom_path + 'set_acl_policy', factory)
#cli_storage_data_plane_command('storage share snapshot', file_service_path + 'snapshot_share', factory, resource_type=ResourceType.DATA_STORAGE, min_api='2017-04-17')

## directory commands
#cli_storage_data_plane_command('storage directory create', file_service_path + 'create_directory', factory, transform=create_boolean_result_output_transformer('created'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage directory delete', file_service_path + 'delete_directory', factory, transform=create_boolean_result_output_transformer('deleted'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage directory show', file_service_path + 'get_directory_properties', factory, table_transformer=transform_file_output, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage directory list', custom_path + 'list_share_directories', factory, transform=transform_file_directory_result, table_transformer=transform_file_output)
#cli_storage_data_plane_command('storage directory exists', file_service_path + 'exists', factory, transform=create_boolean_result_output_transformer('exists'))
#cli_storage_data_plane_command('storage directory metadata show', file_service_path + 'get_directory_metadata', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage directory metadata update', file_service_path + 'set_directory_metadata', factory)

## file commands
#cli_storage_data_plane_command('storage file list', custom_path + 'list_share_files', factory, transform=transform_file_directory_result, table_transformer=transform_file_output)
#cli_storage_data_plane_command('storage file delete', file_service_path + 'delete_file', factory, transform=create_boolean_result_output_transformer('deleted'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage file resize', file_service_path + 'resize_file', factory)
#cli_storage_data_plane_command('storage file url', file_service_path + 'make_file_url', factory, transform=transform_url)
#cli_storage_data_plane_command('storage file generate-sas', file_service_path + 'generate_file_shared_access_signature', factory)
#cli_storage_data_plane_command('storage file show', file_service_path + 'get_file_properties', factory, table_transformer=transform_file_output, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage file update', file_service_path + 'set_file_properties', factory)
#cli_storage_data_plane_command('storage file exists', file_service_path + 'exists', factory, transform=create_boolean_result_output_transformer('exists'))
#cli_storage_data_plane_command('storage file download', file_service_path + 'get_file_to_path', factory)
#cli_storage_data_plane_command('storage file upload', file_service_path + 'create_file_from_path', factory)
#cli_storage_data_plane_command('storage file metadata show', file_service_path + 'get_file_metadata', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage file metadata update', file_service_path + 'set_file_metadata', factory)
#cli_storage_data_plane_command('storage file copy start', file_service_path + 'copy_file', factory)
#cli_storage_data_plane_command('storage file copy cancel', file_service_path + 'abort_copy_file', factory)
#cli_storage_data_plane_command('storage file upload-batch', 'azure.cli.command_modules.storage.file#storage_file_upload_batch', factory)
#cli_storage_data_plane_command('storage file download-batch', 'azure.cli.command_modules.storage.file#storage_file_download_batch', factory)
#cli_storage_data_plane_command('storage file delete-batch', 'azure.cli.command_modules.storage.file#storage_file_delete_batch', factory)
#cli_storage_data_plane_command('storage file copy start-batch', 'azure.cli.command_modules.storage.file#storage_file_copy_batch', factory)

## table commands
#factory = table_data_service_factory
#cli_storage_data_plane_command('storage table generate-sas', table_path + 'generate_table_shared_access_signature', factory)
#cli_storage_data_plane_command('storage table stats', table_path + 'get_table_service_stats', factory, resource_type=ResourceType.DATA_STORAGE, min_api='2016-05-31')
#cli_storage_data_plane_command('storage table list', table_path + 'list_tables', factory, transform=transform_storage_list_output)
#cli_storage_data_plane_command('storage table create', table_path + 'create_table', factory, transform=create_boolean_result_output_transformer('created'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage table exists', table_path + 'exists', factory, transform=create_boolean_result_output_transformer('exists'))
#cli_storage_data_plane_command('storage table delete', table_path + 'delete_table', factory, transform=create_boolean_result_output_transformer('deleted'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage table policy create', custom_path + 'create_acl_policy', factory)
#cli_storage_data_plane_command('storage table policy delete', custom_path + 'delete_acl_policy', factory)
#cli_storage_data_plane_command('storage table policy show', custom_path + 'get_acl_policy', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage table policy list', custom_path + 'list_acl_policies', factory, table_transformer=transform_acl_list_output)
#cli_storage_data_plane_command('storage table policy update', custom_path + 'set_acl_policy', factory)

## table entity commands
#cli_storage_data_plane_command('storage entity query', table_path + 'query_entities', factory, table_transformer=transform_entity_query_output)
#cli_storage_data_plane_command('storage entity show', table_path + 'get_entity', factory, table_transformer=transform_entity_show, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage entity insert', custom_path + 'insert_table_entity', factory)
#cli_storage_data_plane_command('storage entity replace', table_path + 'update_entity', factory)
#cli_storage_data_plane_command('storage entity merge', table_path + 'merge_entity', factory)
#cli_storage_data_plane_command('storage entity delete', table_path + 'delete_entity', factory, transform=create_boolean_result_output_transformer('deleted'), table_transformer=transform_boolean_for_table)

## queue commands
#factory = queue_data_service_factory
#cli_storage_data_plane_command('storage queue generate-sas', queue_path + 'generate_queue_shared_access_signature', factory)
#cli_storage_data_plane_command('storage queue stats', queue_path + 'get_queue_service_stats', factory, resource_type=ResourceType.DATA_STORAGE, min_api='2016-05-31')
#cli_storage_data_plane_command('storage queue list', queue_path + 'list_queues', factory, transform=transform_storage_list_output)
#cli_storage_data_plane_command('storage queue create', queue_path + 'create_queue', factory, transform=create_boolean_result_output_transformer('created'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage queue delete', queue_path + 'delete_queue', factory, transform=create_boolean_result_output_transformer('deleted'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage queue metadata show', queue_path + 'get_queue_metadata', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage queue metadata update', queue_path + 'set_queue_metadata', factory)
#cli_storage_data_plane_command('storage queue exists', queue_path + 'exists', factory, transform=create_boolean_result_output_transformer('exists'))
#cli_storage_data_plane_command('storage queue policy create', custom_path + 'create_acl_policy', factory)
#cli_storage_data_plane_command('storage queue policy delete', custom_path + 'delete_acl_policy', factory)
#cli_storage_data_plane_command('storage queue policy show', custom_path + 'get_acl_policy', factory, exception_handler=_dont_fail_not_exist)
#cli_storage_data_plane_command('storage queue policy list', custom_path + 'list_acl_policies', factory, table_transformer=transform_acl_list_output)
#cli_storage_data_plane_command('storage queue policy update', custom_path + 'set_acl_policy', factory)

## queue message commands
#cli_storage_data_plane_command('storage message put', queue_path + 'put_message', factory)
#cli_storage_data_plane_command('storage message get', queue_path + 'get_messages', factory, table_transformer=transform_message_show)
#cli_storage_data_plane_command('storage message peek', queue_path + 'peek_messages', factory, table_transformer=transform_message_show)
#cli_storage_data_plane_command('storage message delete', queue_path + 'delete_message', factory, transform=create_boolean_result_output_transformer('deleted'), table_transformer=transform_boolean_for_table)
#cli_storage_data_plane_command('storage message clear', queue_path + 'clear_messages', factory)
#cli_storage_data_plane_command('storage message update', queue_path + 'update_message', factory)


## cors commands

#cli_storage_data_plane_command('storage cors add', custom_path + 'add_cors', multi_service_properties_factory)
#cli_storage_data_plane_command('storage cors clear', custom_path + 'clear_cors', multi_service_properties_factory)
#cli_storage_data_plane_command('storage cors list', custom_path + 'list_cors', multi_service_properties_factory,
#                               transform=transform_cors_list_output)

## logging commands
#cli_storage_data_plane_command('storage logging update', custom_path + 'set_logging', multi_service_properties_factory)
#cli_storage_data_plane_command('storage logging show', custom_path + 'get_logging', multi_service_properties_factory,
#                               table_transformer=transform_logging_list_output, exception_handler=_dont_fail_not_exist)

## # metrics commands
#cli_storage_data_plane_command('storage metrics update', custom_path + 'set_metrics', multi_service_properties_factory)
#cli_storage_data_plane_command('storage metrics show', custom_path + 'get_metrics', multi_service_properties_factory,
#                               table_transformer=transform_metrics_list_output, exception_handler=_dont_fail_not_exist)


def load_command_table(self, _):

    storage_account_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.storage.operations.storage_accounts_operations#StorageAccountsOperations.{}',
        client_factory=cf_sa,
        resource_type=ResourceType.MGMT_STORAGE
    )

    cloud_data_plane_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storage.common#CloudStorageAccount.{}',
        client_factory=cloud_storage_account_service_factory
    )

    # region StorageAccount
    with self.command_group('storage account', storage_account_sdk, resource_type=ResourceType.MGMT_STORAGE) as g:
        g.command('check-name', 'check_name_availability')
        g.custom_command('create', 'create_storage_account', min_api='2016-01-01')
        g.custom_command('create', 'create_storage_account_with_account_type', max_api='2015-06-15')
        g.command('delete', 'delete', confirmation=True)
        g.data_plane_command('generate-sas', 'generate_shared_access_signature', command_type=cloud_data_plane_sdk)
        g.command('show', 'get_properties', exception_handler=empty_on_404)
        g.custom_command('list', 'list_storage_accounts')
        g.custom_command('show-usage', 'show_storage_account_usage')
        g.custom_command('show-connection-string', 'show_storage_account_connection_string')
        g.generic_update_command('update', getter_name='get_properties', setter_name='update',
                                 custom_func_name='update_storage_account', min_api='2016-12-01')
        g.command('keys renew', 'regenerate_key', transform=lambda x: getattr(x, 'keys', x))
        g.command('keys list', 'list_keys', transform=lambda x: getattr(x, 'keys', x))

    #with self.command_group('storage account network-rule', storage_account_sdk, min_api='2017-06-01', resource_type=ResourceType.MGMT_STORAGE, storage_client_factory=storage_client_factory(self.cli_ctx).storage_accounts) as g:
    #    g.custom_command('add', 'add_network_rule')
    #    g.custom_command('remove', 'remove_network_rule')
    #    g.custom_command('list', 'list_network_rules')
