# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import cli_command
from azure.cli.command_modules.storage._command_type import cli_storage_data_plane_command

from azure.cli.command_modules.storage._factory import \
    (storage_client_factory, blob_data_service_factory, file_data_service_factory,
     table_data_service_factory, queue_data_service_factory, cloud_storage_account_service_factory)
from azure.cli.command_modules.storage._validators import \
    (transform_acl_list_output, transform_cors_list_output, transform_entity_query_output,
     transform_logging_list_output, transform_metrics_list_output,
     transform_url, transform_storage_list_output, transform_storage_exists_output,
     transform_storage_boolean_output, transform_container_permission_output)
from azure.cli.command_modules.storage._format import \
    (transform_container_list, transform_container_show,
     transform_blob_output,
     transform_share_list,
     transform_file_output,
     transform_entity_show,
     transform_message_show,
     transform_boolean_for_table)

# storage account commands
factory = lambda kwargs: storage_client_factory().storage_accounts
cli_command(__name__, 'storage account check-name', 'azure.mgmt.storage.operations.storage_accounts_operations#StorageAccountsOperations.check_name_availability', factory)
cli_command(__name__, 'storage account delete', 'azure.mgmt.storage.operations.storage_accounts_operations#StorageAccountsOperations.delete', factory)
cli_command(__name__, 'storage account show', 'azure.mgmt.storage.operations.storage_accounts_operations#StorageAccountsOperations.get_properties', factory)
cli_command(__name__, 'storage account create', 'azure.cli.command_modules.storage.custom#create_storage_account')
cli_command(__name__, 'storage account list', 'azure.cli.command_modules.storage.custom#list_storage_accounts')
cli_command(__name__, 'storage account show-usage', 'azure.cli.command_modules.storage.custom#show_storage_account_usage')
cli_command(__name__, 'storage account update', 'azure.cli.command_modules.storage.custom#set_storage_account_properties')
cli_command(__name__, 'storage account show-connection-string', 'azure.cli.command_modules.storage.custom#show_storage_account_connection_string')
cli_command(__name__, 'storage account keys renew', 'azure.mgmt.storage.operations.storage_accounts_operations#StorageAccountsOperations.regenerate_key', factory)
cli_command(__name__, 'storage account keys list', 'azure.mgmt.storage.operations.storage_accounts_operations#StorageAccountsOperations.list_keys', factory)
cli_storage_data_plane_command('storage account generate-sas', 'azure.storage.cloudstorageaccount#CloudStorageAccount.generate_shared_access_signature', cloud_storage_account_service_factory)

# container commands
factory = blob_data_service_factory
cli_storage_data_plane_command('storage container list', 'azure.storage.blob.blockblobservice#BlockBlobService.list_containers', factory, transform=transform_storage_list_output, table_transformer=transform_container_list)
cli_storage_data_plane_command('storage container delete', 'azure.storage.blob.blockblobservice#BlockBlobService.delete_container', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage container show', 'azure.storage.blob.blockblobservice#BlockBlobService.get_container_properties', factory, table_transformer=transform_container_show)
cli_storage_data_plane_command('storage container create', 'azure.storage.blob.blockblobservice#BlockBlobService.create_container', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage container generate-sas', 'azure.storage.blob.blockblobservice#BlockBlobService.generate_container_shared_access_signature', factory)
cli_storage_data_plane_command('storage container metadata update', 'azure.storage.blob.blockblobservice#BlockBlobService.set_container_metadata', factory)
cli_storage_data_plane_command('storage container metadata show', 'azure.storage.blob.blockblobservice#BlockBlobService.get_container_metadata', factory)
cli_storage_data_plane_command('storage container lease acquire', 'azure.storage.blob.blockblobservice#BlockBlobService.acquire_container_lease', factory)
cli_storage_data_plane_command('storage container lease renew', 'azure.storage.blob.blockblobservice#BlockBlobService.renew_container_lease', factory)
cli_storage_data_plane_command('storage container lease release', 'azure.storage.blob.blockblobservice#BlockBlobService.release_container_lease', factory)
cli_storage_data_plane_command('storage container lease change', 'azure.storage.blob.blockblobservice#BlockBlobService.change_container_lease', factory)
cli_storage_data_plane_command('storage container lease break', 'azure.storage.blob.blockblobservice#BlockBlobService.break_container_lease', factory)
cli_storage_data_plane_command('storage container exists', 'azure.storage.blob.baseblobservice#BaseBlobService.exists', factory, transform=transform_storage_exists_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage container set-permission', 'azure.storage.blob.baseblobservice#BaseBlobService.set_container_acl', factory)
cli_storage_data_plane_command('storage container show-permission', 'azure.storage.blob.baseblobservice#BaseBlobService.get_container_acl', factory, transform=transform_container_permission_output)
cli_storage_data_plane_command('storage container policy create', 'azure.cli.command_modules.storage.custom#create_acl_policy', factory)
cli_storage_data_plane_command('storage container policy delete', 'azure.cli.command_modules.storage.custom#delete_acl_policy', factory)
cli_storage_data_plane_command('storage container policy show', 'azure.cli.command_modules.storage.custom#get_acl_policy', factory)
cli_storage_data_plane_command('storage container policy list', 'azure.cli.command_modules.storage.custom#list_acl_policies', factory, table_transformer=transform_acl_list_output)
cli_storage_data_plane_command('storage container policy update', 'azure.cli.command_modules.storage.custom#set_acl_policy', factory)

# blob commands
cli_storage_data_plane_command('storage blob list', 'azure.storage.blob.blockblobservice#BlockBlobService.list_blobs', factory, transform=transform_storage_list_output, table_transformer=transform_blob_output)
cli_storage_data_plane_command('storage blob delete', 'azure.storage.blob.blockblobservice#BlockBlobService.delete_blob', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage blob generate-sas', 'azure.storage.blob.blockblobservice#BlockBlobService.generate_blob_shared_access_signature', factory)
cli_storage_data_plane_command('storage blob url', 'azure.storage.blob.blockblobservice#BlockBlobService.make_blob_url', factory, transform=transform_url)
cli_storage_data_plane_command('storage blob snapshot', 'azure.storage.blob.blockblobservice#BlockBlobService.snapshot_blob', factory)
cli_storage_data_plane_command('storage blob show', 'azure.storage.blob.blockblobservice#BlockBlobService.get_blob_properties', factory, table_transformer=transform_blob_output)
cli_storage_data_plane_command('storage blob update', 'azure.storage.blob.blockblobservice#BlockBlobService.set_blob_properties', factory)
cli_storage_data_plane_command('storage blob exists', 'azure.storage.blob.baseblobservice#BaseBlobService.exists', factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage blob download', 'azure.storage.blob.baseblobservice#BaseBlobService.get_blob_to_path', factory)
cli_storage_data_plane_command('storage blob upload', 'azure.cli.command_modules.storage.custom#upload_blob', factory)
cli_storage_data_plane_command('storage blob metadata show', 'azure.storage.blob.blockblobservice#BlockBlobService.get_blob_metadata', factory)
cli_storage_data_plane_command('storage blob metadata update', 'azure.storage.blob.blockblobservice#BlockBlobService.set_blob_metadata', factory)
cli_storage_data_plane_command('storage blob service-properties show', 'azure.storage.blob.baseblobservice#BaseBlobService.get_blob_service_properties', factory)
cli_storage_data_plane_command('storage blob lease acquire', 'azure.storage.blob.blockblobservice#BlockBlobService.acquire_blob_lease', factory)
cli_storage_data_plane_command('storage blob lease renew', 'azure.storage.blob.blockblobservice#BlockBlobService.renew_blob_lease', factory)
cli_storage_data_plane_command('storage blob lease release', 'azure.storage.blob.blockblobservice#BlockBlobService.release_blob_lease', factory)
cli_storage_data_plane_command('storage blob lease change', 'azure.storage.blob.blockblobservice#BlockBlobService.change_blob_lease', factory)
cli_storage_data_plane_command('storage blob lease break', 'azure.storage.blob.blockblobservice#BlockBlobService.break_blob_lease', factory)
cli_storage_data_plane_command('storage blob copy start', 'azure.storage.blob.blockblobservice#BlockBlobService.copy_blob', factory)
cli_storage_data_plane_command('storage blob copy start-batch', 'azure.cli.command_modules.storage.blob#storage_blob_copy_batch', factory)
cli_storage_data_plane_command('storage blob copy cancel', 'azure.storage.blob.blockblobservice#BlockBlobService.abort_copy_blob', factory)

cli_storage_data_plane_command('storage blob upload-batch',
                               'azure.cli.command_modules.storage.blob#storage_blob_upload_batch',
                               factory)

cli_storage_data_plane_command('storage blob download-batch',
                               'azure.cli.command_modules.storage.blob#storage_blob_download_batch',
                               factory)

# share commands
factory = file_data_service_factory
cli_storage_data_plane_command('storage share list', 'azure.storage.file.fileservice#FileService.list_shares', factory, transform=transform_storage_list_output, table_transformer=transform_share_list)
cli_storage_data_plane_command('storage share create', 'azure.storage.file.fileservice#FileService.create_share', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage share delete', 'azure.storage.file.fileservice#FileService.delete_share', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage share generate-sas', 'azure.storage.file.fileservice#FileService.generate_share_shared_access_signature', factory)
cli_storage_data_plane_command('storage share stats', 'azure.storage.file.fileservice#FileService.get_share_stats', factory)
cli_storage_data_plane_command('storage share show', 'azure.storage.file.fileservice#FileService.get_share_properties', factory)
cli_storage_data_plane_command('storage share update', 'azure.storage.file.fileservice#FileService.set_share_properties', factory)
cli_storage_data_plane_command('storage share metadata show', 'azure.storage.file.fileservice#FileService.get_share_metadata', factory)
cli_storage_data_plane_command('storage share metadata update', 'azure.storage.file.fileservice#FileService.set_share_metadata', factory)
cli_storage_data_plane_command('storage share exists', 'azure.storage.file.fileservice#FileService.exists', factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage share policy create', 'azure.cli.command_modules.storage.custom#create_acl_policy', factory)
cli_storage_data_plane_command('storage share policy delete', 'azure.cli.command_modules.storage.custom#delete_acl_policy', factory)
cli_storage_data_plane_command('storage share policy show', 'azure.cli.command_modules.storage.custom#get_acl_policy', factory)
cli_storage_data_plane_command('storage share policy list', 'azure.cli.command_modules.storage.custom#list_acl_policies', factory, table_transformer=transform_acl_list_output)
cli_storage_data_plane_command('storage share policy update', 'azure.cli.command_modules.storage.custom#set_acl_policy', factory)

# directory commands
cli_storage_data_plane_command('storage directory create', 'azure.storage.file.fileservice#FileService.create_directory', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage directory delete', 'azure.storage.file.fileservice#FileService.delete_directory', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage directory show', 'azure.storage.file.fileservice#FileService.get_directory_properties', factory, table_transformer=transform_file_output)
cli_storage_data_plane_command('storage directory exists', 'azure.storage.file.fileservice#FileService.exists', factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage directory metadata show', 'azure.storage.file.fileservice#FileService.get_directory_metadata', factory)
cli_storage_data_plane_command('storage directory metadata update', 'azure.storage.file.fileservice#FileService.set_directory_metadata', factory)

# file commands
cli_storage_data_plane_command('storage file list', 'azure.storage.file.fileservice#FileService.list_directories_and_files', factory, table_transformer=transform_file_output)
cli_storage_data_plane_command('storage file delete', 'azure.storage.file.fileservice#FileService.delete_file', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage file resize', 'azure.storage.file.fileservice#FileService.resize_file', factory)
cli_storage_data_plane_command('storage file url', 'azure.storage.file.fileservice#FileService.make_file_url', factory, transform=transform_url)
cli_storage_data_plane_command('storage file generate-sas', 'azure.storage.file.fileservice#FileService.generate_file_shared_access_signature', factory)
cli_storage_data_plane_command('storage file show', 'azure.storage.file.fileservice#FileService.get_file_properties', factory, table_transformer=transform_file_output)
cli_storage_data_plane_command('storage file update', 'azure.storage.file.fileservice#FileService.set_file_properties', factory)
cli_storage_data_plane_command('storage file exists', 'azure.storage.file.fileservice#FileService.exists', factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage file download', 'azure.storage.file.fileservice#FileService.get_file_to_path', factory)
cli_storage_data_plane_command('storage file upload', 'azure.storage.file.fileservice#FileService.create_file_from_path', factory)
cli_storage_data_plane_command('storage file metadata show', 'azure.storage.file.fileservice#FileService.get_file_metadata', factory)
cli_storage_data_plane_command('storage file metadata update', 'azure.storage.file.fileservice#FileService.set_file_metadata', factory)
cli_storage_data_plane_command('storage file copy start', 'azure.storage.file.fileservice#FileService.copy_file', factory)
cli_storage_data_plane_command('storage file copy cancel', 'azure.storage.file.fileservice#FileService.abort_copy_file', factory)

cli_storage_data_plane_command('storage file upload-batch',
                               'azure.cli.command_modules.storage.file#storage_file_upload_batch',
                               factory)

cli_storage_data_plane_command('storage file download-batch',
                               'azure.cli.command_modules.storage.file#storage_file_download_batch',
                               factory)

cli_storage_data_plane_command('storage file copy start-batch',
                               'azure.cli.command_modules.storage.file#storage_file_copy_batch',
                               factory)

# table commands
factory = table_data_service_factory
cli_storage_data_plane_command('storage table generate-sas', 'azure.storage.table.tableservice#TableService.generate_table_shared_access_signature', factory)
cli_storage_data_plane_command('storage table stats', 'azure.storage.table.tableservice#TableService.get_table_service_stats', factory)
cli_storage_data_plane_command('storage table list', 'azure.storage.table.tableservice#TableService.list_tables', factory, transform=transform_storage_list_output)
cli_storage_data_plane_command('storage table create', 'azure.storage.table.tableservice#TableService.create_table', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage table exists', 'azure.storage.table.tableservice#TableService.exists', factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage table delete', 'azure.storage.table.tableservice#TableService.delete_table', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage table policy create', 'azure.cli.command_modules.storage.custom#create_acl_policy', factory)
cli_storage_data_plane_command('storage table policy delete', 'azure.cli.command_modules.storage.custom#delete_acl_policy', factory)
cli_storage_data_plane_command('storage table policy show', 'azure.cli.command_modules.storage.custom#get_acl_policy', factory)
cli_storage_data_plane_command('storage table policy list', 'azure.cli.command_modules.storage.custom#list_acl_policies', factory, table_transformer=transform_acl_list_output)
cli_storage_data_plane_command('storage table policy update', 'azure.cli.command_modules.storage.custom#set_acl_policy', factory)

# table entity commands
cli_storage_data_plane_command('storage entity query', 'azure.storage.table.tableservice#TableService.query_entities', factory, table_transformer=transform_entity_query_output)
cli_storage_data_plane_command('storage entity show', 'azure.storage.table.tableservice#TableService.get_entity', factory, table_transformer=transform_entity_show)
cli_storage_data_plane_command('storage entity insert', 'azure.cli.command_modules.storage.custom#insert_table_entity', factory)
cli_storage_data_plane_command('storage entity replace', 'azure.storage.table.tableservice#TableService.update_entity', factory)
cli_storage_data_plane_command('storage entity merge', 'azure.storage.table.tableservice#TableService.merge_entity', factory)
cli_storage_data_plane_command('storage entity delete', 'azure.storage.table.tableservice#TableService.delete_entity', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)

# queue commands
factory = queue_data_service_factory
cli_storage_data_plane_command('storage queue generate-sas', 'azure.storage.queue.queueservice#QueueService.generate_queue_shared_access_signature', factory)
cli_storage_data_plane_command('storage queue stats', 'azure.storage.queue.queueservice#QueueService.get_queue_service_stats', factory)
cli_storage_data_plane_command('storage queue list', 'azure.storage.queue.queueservice#QueueService.list_queues', factory, transform=transform_storage_list_output)
cli_storage_data_plane_command('storage queue create', 'azure.storage.queue.queueservice#QueueService.create_queue', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage queue delete', 'azure.storage.queue.queueservice#QueueService.delete_queue', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage queue metadata show', 'azure.storage.queue.queueservice#QueueService.get_queue_metadata', factory)
cli_storage_data_plane_command('storage queue metadata update', 'azure.storage.queue.queueservice#QueueService.set_queue_metadata', factory)
cli_storage_data_plane_command('storage queue exists', 'azure.storage.queue.queueservice#QueueService.exists', factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage queue policy create', 'azure.cli.command_modules.storage.custom#create_acl_policy', factory)
cli_storage_data_plane_command('storage queue policy delete', 'azure.cli.command_modules.storage.custom#delete_acl_policy', factory)
cli_storage_data_plane_command('storage queue policy show', 'azure.cli.command_modules.storage.custom#get_acl_policy', factory)
cli_storage_data_plane_command('storage queue policy list', 'azure.cli.command_modules.storage.custom#list_acl_policies', factory, table_transformer=transform_acl_list_output)
cli_storage_data_plane_command('storage queue policy update', 'azure.cli.command_modules.storage.custom#set_acl_policy', factory)

# queue message commands
cli_storage_data_plane_command('storage message put', 'azure.storage.queue.queueservice#QueueService.put_message', factory)
cli_storage_data_plane_command('storage message get', 'azure.storage.queue.queueservice#QueueService.get_messages', factory, table_transformer=transform_message_show)
cli_storage_data_plane_command('storage message peek', 'azure.storage.queue.queueservice#QueueService.peek_messages', factory, table_transformer=transform_message_show)
cli_storage_data_plane_command('storage message delete', 'azure.storage.queue.queueservice#QueueService.delete_message', factory, transform=transform_storage_boolean_output, table_transformer=transform_boolean_for_table)
cli_storage_data_plane_command('storage message clear', 'azure.storage.queue.queueservice#QueueService.clear_messages', factory)
cli_storage_data_plane_command('storage message update', 'azure.storage.queue.queueservice#QueueService.update_message', factory)

# cors commands
cli_storage_data_plane_command('storage cors list', 'azure.cli.command_modules.storage.custom#list_cors', None, transform=transform_cors_list_output)
cli_storage_data_plane_command('storage cors add', 'azure.cli.command_modules.storage.custom#add_cors', None)
cli_storage_data_plane_command('storage cors clear', 'azure.cli.command_modules.storage.custom#clear_cors', None)

# logging commands
cli_storage_data_plane_command('storage logging show', 'azure.cli.command_modules.storage.custom#get_logging', None, table_transformer=transform_logging_list_output)
cli_storage_data_plane_command('storage logging update', 'azure.cli.command_modules.storage.custom#set_logging', None)

# metrics commands
cli_storage_data_plane_command('storage metrics show', 'azure.cli.command_modules.storage.custom#get_metrics', None, table_transformer=transform_metrics_list_output)
cli_storage_data_plane_command('storage metrics update', 'azure.cli.command_modules.storage.custom#set_metrics', None)
