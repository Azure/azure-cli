#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from __future__ import print_function

from azure.mgmt.storage.operations import StorageAccountsOperations
from azure.storage.blob import BlockBlobService
from azure.storage.blob.baseblobservice import BaseBlobService
from azure.storage.file import FileService
from azure.storage.table import TableService
from azure.storage.queue import QueueService
from azure.storage import CloudStorageAccount

from azure.cli.core.commands import cli_command

from azure.cli.command_modules.storage._command_type import cli_storage_data_plane_command
from azure.cli.command_modules.storage._factory import \
    (storage_client_factory, blob_data_service_factory, file_data_service_factory,
     table_data_service_factory, queue_data_service_factory, cloud_storage_account_service_factory)
from azure.cli.command_modules.storage.custom import \
    (create_storage_account, list_storage_accounts, show_storage_account_usage,
     set_storage_account_properties, show_storage_account_connection_string,
     upload_blob, get_acl_policy,
     create_acl_policy, delete_acl_policy, list_acl_policies, set_acl_policy,
     insert_table_entity, list_cors, add_cors, clear_cors,
     get_logging, set_logging, get_metrics, set_metrics)
from azure.cli.command_modules.storage._validators import \
    (transform_acl_list_output, transform_cors_list_output, transform_entity_query_output,
     transform_file_list_output, transform_logging_list_output, transform_metrics_list_output,
     transform_url, transform_storage_list_output, transform_storage_exists_output,
     transform_storage_boolean_output, transform_container_permission_output)

# storage account commands
factory = lambda kwargs: storage_client_factory().storage_accounts
cli_command('storage account check-name', StorageAccountsOperations.check_name_availability, factory)
cli_command('storage account delete', StorageAccountsOperations.delete, factory)
cli_command('storage account show', StorageAccountsOperations.get_properties, factory)
cli_command('storage account create', create_storage_account)
cli_command('storage account list', list_storage_accounts)
cli_command('storage account show-usage', show_storage_account_usage)
cli_command('storage account update', set_storage_account_properties)
cli_command('storage account show-connection-string', show_storage_account_connection_string)
cli_command('storage account keys renew', StorageAccountsOperations.regenerate_key, factory)
cli_command('storage account keys list', StorageAccountsOperations.list_keys, factory)
cli_storage_data_plane_command('storage account generate-sas', CloudStorageAccount.generate_shared_access_signature, cloud_storage_account_service_factory)

# container commands
factory = blob_data_service_factory
cli_storage_data_plane_command('storage container list', BlockBlobService.list_containers, factory, transform=transform_storage_list_output)
cli_storage_data_plane_command('storage container delete', BlockBlobService.delete_container, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage container show', BlockBlobService.get_container_properties, factory)
cli_storage_data_plane_command('storage container create', BlockBlobService.create_container, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage container generate-sas', BlockBlobService.generate_container_shared_access_signature, factory)
cli_storage_data_plane_command('storage container metadata update', BlockBlobService.set_container_metadata, factory)
cli_storage_data_plane_command('storage container metadata show', BlockBlobService.get_container_metadata, factory)
cli_storage_data_plane_command('storage container lease acquire', BlockBlobService.acquire_container_lease, factory)
cli_storage_data_plane_command('storage container lease renew', BlockBlobService.renew_container_lease, factory)
cli_storage_data_plane_command('storage container lease release', BlockBlobService.release_container_lease, factory)
cli_storage_data_plane_command('storage container lease change', BlockBlobService.change_container_lease, factory)
cli_storage_data_plane_command('storage container lease break', BlockBlobService.break_container_lease, factory)
cli_storage_data_plane_command('storage container exists', BaseBlobService.exists, factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage container set-permission', BaseBlobService.set_container_acl, factory)
cli_storage_data_plane_command('storage container show-permission', BaseBlobService.get_container_acl, factory, transform=transform_container_permission_output)
cli_storage_data_plane_command('storage container policy create', create_acl_policy, factory)
cli_storage_data_plane_command('storage container policy delete', delete_acl_policy, factory)
cli_storage_data_plane_command('storage container policy show', get_acl_policy, factory)
cli_storage_data_plane_command('storage container policy list', list_acl_policies, factory, table_transformer=transform_acl_list_output)
cli_storage_data_plane_command('storage container policy update', set_acl_policy, factory)

# blob commands
cli_storage_data_plane_command('storage blob list', BlockBlobService.list_blobs, factory, transform=transform_storage_list_output)
cli_storage_data_plane_command('storage blob delete', BlockBlobService.delete_blob, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage blob generate-sas', BlockBlobService.generate_blob_shared_access_signature, factory)
cli_storage_data_plane_command('storage blob url', BlockBlobService.make_blob_url, factory, transform=transform_url)
cli_storage_data_plane_command('storage blob snapshot', BlockBlobService.snapshot_blob, factory)
cli_storage_data_plane_command('storage blob show', BlockBlobService.get_blob_properties, factory)
cli_storage_data_plane_command('storage blob update', BlockBlobService.set_blob_properties, factory)
cli_storage_data_plane_command('storage blob exists', BaseBlobService.exists, factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage blob download', BaseBlobService.get_blob_to_path, factory)
cli_storage_data_plane_command('storage blob upload', upload_blob, factory)
cli_storage_data_plane_command('storage blob metadata show', BlockBlobService.get_blob_metadata, factory)
cli_storage_data_plane_command('storage blob metadata update', BlockBlobService.set_blob_metadata, factory)
cli_storage_data_plane_command('storage blob service-properties show', BaseBlobService.get_blob_service_properties, factory)
cli_storage_data_plane_command('storage blob lease acquire', BlockBlobService.acquire_blob_lease, factory)
cli_storage_data_plane_command('storage blob lease renew', BlockBlobService.renew_blob_lease, factory)
cli_storage_data_plane_command('storage blob lease release', BlockBlobService.release_blob_lease, factory)
cli_storage_data_plane_command('storage blob lease change', BlockBlobService.change_blob_lease, factory)
cli_storage_data_plane_command('storage blob lease break', BlockBlobService.break_blob_lease, factory)
cli_storage_data_plane_command('storage blob copy start', BlockBlobService.copy_blob, factory)
cli_storage_data_plane_command('storage blob copy cancel', BlockBlobService.abort_copy_blob, factory)

# share commands
factory = file_data_service_factory
cli_storage_data_plane_command('storage share list', FileService.list_shares, factory, transform=transform_storage_list_output)
cli_storage_data_plane_command('storage share create', FileService.create_share, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage share delete', FileService.delete_share, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage share generate-sas', FileService.generate_share_shared_access_signature, factory)
cli_storage_data_plane_command('storage share stats', FileService.get_share_stats, factory)
cli_storage_data_plane_command('storage share show', FileService.get_share_properties, factory)
cli_storage_data_plane_command('storage share update', FileService.set_share_properties, factory)
cli_storage_data_plane_command('storage share metadata show', FileService.get_share_metadata, factory)
cli_storage_data_plane_command('storage share metadata update', FileService.set_share_metadata, factory)
cli_storage_data_plane_command('storage share exists', FileService.exists, factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage share policy create', create_acl_policy, factory)
cli_storage_data_plane_command('storage share policy delete', delete_acl_policy, factory)
cli_storage_data_plane_command('storage share policy show', get_acl_policy, factory)
cli_storage_data_plane_command('storage share policy list', list_acl_policies, factory, table_transformer=transform_acl_list_output)
cli_storage_data_plane_command('storage share policy update', set_acl_policy, factory)

# directory commands
cli_storage_data_plane_command('storage directory create', FileService.create_directory, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage directory delete', FileService.delete_directory, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage directory show', FileService.get_directory_properties, factory)
cli_storage_data_plane_command('storage directory exists', FileService.exists, factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage directory metadata show', FileService.get_directory_metadata, factory)
cli_storage_data_plane_command('storage directory metadata update', FileService.set_directory_metadata, factory)

# file commands
cli_storage_data_plane_command('storage file list', FileService.list_directories_and_files, factory, table_transformer=transform_file_list_output)
cli_storage_data_plane_command('storage file delete', FileService.delete_file, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage file resize', FileService.resize_file, factory)
cli_storage_data_plane_command('storage file url', FileService.make_file_url, factory, transform=transform_url)
cli_storage_data_plane_command('storage file generate-sas', FileService.generate_file_shared_access_signature, factory)
cli_storage_data_plane_command('storage file show', FileService.get_file_properties, factory)
cli_storage_data_plane_command('storage file update', FileService.set_file_properties, factory)
cli_storage_data_plane_command('storage file exists', FileService.exists, factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage file download', FileService.get_file_to_path, factory)
cli_storage_data_plane_command('storage file upload', FileService.create_file_from_path, factory)
cli_storage_data_plane_command('storage file metadata show', FileService.get_file_metadata, factory)
cli_storage_data_plane_command('storage file metadata update', FileService.set_file_metadata, factory)
cli_storage_data_plane_command('storage file copy start', FileService.copy_file, factory)
cli_storage_data_plane_command('storage file copy cancel', FileService.abort_copy_file, factory)

# table commands
factory = table_data_service_factory
cli_storage_data_plane_command('storage table generate-sas', TableService.generate_table_shared_access_signature, factory)
cli_storage_data_plane_command('storage table stats', TableService.get_table_service_stats, factory)
cli_storage_data_plane_command('storage table list', TableService.list_tables, factory, transform=transform_storage_list_output)
cli_storage_data_plane_command('storage table create', TableService.create_table, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage table exists', TableService.exists, factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage table delete', TableService.delete_table, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage table policy create', create_acl_policy, factory)
cli_storage_data_plane_command('storage table policy delete', delete_acl_policy, factory)
cli_storage_data_plane_command('storage table policy show', get_acl_policy, factory)
cli_storage_data_plane_command('storage table policy list', list_acl_policies, factory, table_transformer=transform_acl_list_output)
cli_storage_data_plane_command('storage table policy update', set_acl_policy, factory)

# table entity commands
cli_storage_data_plane_command('storage entity query', TableService.query_entities, factory, table_transformer=transform_entity_query_output)
cli_storage_data_plane_command('storage entity show', TableService.get_entity, factory)
cli_storage_data_plane_command('storage entity insert', insert_table_entity, factory)
cli_storage_data_plane_command('storage entity replace', TableService.update_entity, factory)
cli_storage_data_plane_command('storage entity merge', TableService.merge_entity, factory)
cli_storage_data_plane_command('storage entity delete', TableService.delete_entity, factory, transform=transform_storage_boolean_output)

# queue commands
factory = queue_data_service_factory
cli_storage_data_plane_command('storage queue generate-sas', QueueService.generate_queue_shared_access_signature, factory)
cli_storage_data_plane_command('storage queue stats', QueueService.get_queue_service_stats, factory)
cli_storage_data_plane_command('storage queue list', QueueService.list_queues, factory, transform=transform_storage_list_output)
cli_storage_data_plane_command('storage queue create', QueueService.create_queue, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage queue delete', QueueService.delete_queue, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage queue metadata show', QueueService.get_queue_metadata, factory)
cli_storage_data_plane_command('storage queue metadata update', QueueService.set_queue_metadata, factory)
cli_storage_data_plane_command('storage queue exists', QueueService.exists, factory, transform=transform_storage_exists_output)
cli_storage_data_plane_command('storage queue policy create', create_acl_policy, factory)
cli_storage_data_plane_command('storage queue policy delete', delete_acl_policy, factory)
cli_storage_data_plane_command('storage queue policy show', get_acl_policy, factory)
cli_storage_data_plane_command('storage queue policy list', list_acl_policies, factory, table_transformer=transform_acl_list_output)
cli_storage_data_plane_command('storage queue policy update', set_acl_policy, factory)

# queue message commands
cli_storage_data_plane_command('storage message put', QueueService.put_message, factory)
cli_storage_data_plane_command('storage message get', QueueService.get_messages, factory)
cli_storage_data_plane_command('storage message peek', QueueService.peek_messages, factory)
cli_storage_data_plane_command('storage message delete', QueueService.delete_message, factory, transform=transform_storage_boolean_output)
cli_storage_data_plane_command('storage message clear', QueueService.clear_messages, factory)
cli_storage_data_plane_command('storage message update', QueueService.update_message, factory)

# cors commands
cli_storage_data_plane_command('storage cors list', list_cors, None, transform=transform_cors_list_output)
cli_storage_data_plane_command('storage cors add', add_cors, None)
cli_storage_data_plane_command('storage cors clear', clear_cors, None)

# logging commands
cli_storage_data_plane_command('storage logging show', get_logging, None, table_transformer=transform_logging_list_output)
cli_storage_data_plane_command('storage logging update', set_logging, None)

# metrics commands
cli_storage_data_plane_command('storage metrics show', get_metrics, None, table_transformer=transform_metrics_list_output)
cli_storage_data_plane_command('storage metrics update', set_metrics, None)
