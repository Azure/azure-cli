from __future__ import print_function

from azure.cli.commands import CommandTable, patch_aliases
from azure.cli.commands._auto_command import build_operation, CommandDefinition, cli_command

from azure.mgmt.storage.operations import StorageAccountsOperations
from azure.storage.blob import BlockBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount

from azure.cli.command_modules.storage._command_type import cli_storage_data_plane_command
from azure.cli.command_modules.storage._factory import \
    (storage_client_factory, blob_data_service_factory, file_data_service_factory,
     cloud_storage_account_service_factory)
from azure.cli.command_modules.storage.custom import \
    (ConvenienceStorageAccountCommands, ConvenienceBlobServiceCommands,
     ConvenienceFileServiceCommands)

command_table = CommandTable()

# storage account commands
factory = lambda **kwargs: storage_client_factory(**kwargs).storage_accounts
cli_command('storage account check-name', factory, StorageAccountsOperations.check_name_availability, 'Result', command_table)
cli_command('storage account delete', factory, StorageAccountsOperations.delete, None, command_table)
cli_command('storage account show', factory, StorageAccountsOperations.get_properties, 'StorageAccount', command_table)
cli_command('storage account keys list', factory, StorageAccountsOperations.list_keys, '[StorageAccountKeys]', command_table)
cli_command('storage account create', None, ConvenienceStorageAccountCommands.create, 'Result', command_table)
cli_command('storage account list', None, ConvenienceStorageAccountCommands.list, '[StorageAccount]', command_table)
cli_command('storage account show-usage', None, ConvenienceStorageAccountCommands.show_usage, 'Result', command_table)
cli_command('storage account set', None, ConvenienceStorageAccountCommands.set, 'Result', command_table)
cli_command('storage account connection-string', None, ConvenienceStorageAccountCommands.connection_string, 'Result', command_table)
cli_command('storage account keys renew', None, ConvenienceStorageAccountCommands.renew_keys, '[StorageAccountKeys]', command_table)
cli_storage_data_plane_command(command_table, 'storage account generate-sas', CloudStorageAccount.generate_shared_access_signature, 'SAS', cloud_storage_account_service_factory)

# container commands
factory = blob_data_service_factory
cli_storage_data_plane_command(command_table, 'storage container list', BlockBlobService.list_containers, '[Container]', factory)
cli_storage_data_plane_command(command_table, 'storage container delete', BlockBlobService.delete_container, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage container show', BlockBlobService.get_container_properties, 'ContainerProperties', factory)
cli_storage_data_plane_command(command_table, 'storage container create', BlockBlobService.create_container, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage container generate-sas', BlockBlobService.generate_container_shared_access_signature, 'SAS', factory)
cli_storage_data_plane_command(command_table, 'storage container metadata set', BlockBlobService.set_container_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage container metadata show', BlockBlobService.get_container_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage container lease acquire', BlockBlobService.acquire_container_lease, 'LeaseID', factory)
cli_storage_data_plane_command(command_table, 'storage container lease renew', BlockBlobService.renew_container_lease, None, factory)
cli_storage_data_plane_command(command_table, 'storage container lease release', BlockBlobService.release_container_lease, None, factory)
cli_storage_data_plane_command(command_table, 'storage container lease change', BlockBlobService.change_container_lease, None, factory)
cli_storage_data_plane_command(command_table, 'storage container lease break', BlockBlobService.break_container_lease, 'Int', factory)
cli_storage_data_plane_command(command_table, 'storage container exists', ConvenienceBlobServiceCommands.container_exists, 'Bool', factory)

# blob commands
cli_storage_data_plane_command(command_table, 'storage blob list', BlockBlobService.list_blobs, '[Blob]', factory)
cli_storage_data_plane_command(command_table, 'storage blob delete', BlockBlobService.delete_blob, None, factory)
cli_storage_data_plane_command(command_table, 'storage blob generate-sas', BlockBlobService.generate_blob_shared_access_signature, 'SAS', factory)
cli_storage_data_plane_command(command_table, 'storage blob url', BlockBlobService.make_blob_url, 'URL', factory)
cli_storage_data_plane_command(command_table, 'storage blob snapshot', BlockBlobService.snapshot_blob, 'SnapshotProperties', factory)
cli_storage_data_plane_command(command_table, 'storage blob show', BlockBlobService.get_blob_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage blob set', BlockBlobService.set_blob_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage blob exists', ConvenienceBlobServiceCommands.blob_exists, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage blob download', ConvenienceBlobServiceCommands.download, 'Results', factory)
cli_storage_data_plane_command(command_table, 'storage blob upload', ConvenienceBlobServiceCommands.upload, 'Results', factory)
cli_storage_data_plane_command(command_table, 'storage blob service-properties show', BlockBlobService.get_blob_service_properties, '[ServiceProperties]', factory)
cli_storage_data_plane_command(command_table, 'storage blob service-properties set', BlockBlobService.set_blob_service_properties, 'ServiceProperties', factory)
cli_storage_data_plane_command(command_table, 'storage blob metadata show', BlockBlobService.get_blob_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage blob metadata set', BlockBlobService.set_blob_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage blob lease acquire', BlockBlobService.acquire_blob_lease, 'LeaseID', factory)
cli_storage_data_plane_command(command_table, 'storage blob lease renew', BlockBlobService.renew_blob_lease, 'LeaseID', factory)
cli_storage_data_plane_command(command_table, 'storage blob lease release', BlockBlobService.release_blob_lease, None, factory)
cli_storage_data_plane_command(command_table, 'storage blob lease change', BlockBlobService.change_blob_lease, None, factory)
cli_storage_data_plane_command(command_table, 'storage blob lease break', BlockBlobService.break_blob_lease, 'Int', factory)
cli_storage_data_plane_command(command_table, 'storage blob copy start', BlockBlobService.copy_blob, 'CopyOperationProperties', factory)
cli_storage_data_plane_command(command_table, 'storage blob copy cancel', BlockBlobService.abort_copy_blob, None, factory)

# share commands
factory = file_data_service_factory
cli_storage_data_plane_command(command_table, 'storage share list', FileService.list_shares, '[Share]', factory)
cli_storage_data_plane_command(command_table, 'storage share contents', FileService.list_directories_and_files, '[ShareContents]', factory)
cli_storage_data_plane_command(command_table, 'storage share create', FileService.create_share, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage share delete', FileService.delete_share, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage share generate-sas', FileService.generate_share_shared_access_signature, 'SAS', factory)
cli_storage_data_plane_command(command_table, 'storage share stats', FileService.get_share_stats, 'ShareStats', factory)
cli_storage_data_plane_command(command_table, 'storage share show', FileService.get_share_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage share set', FileService.set_share_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage share metadata show', FileService.get_share_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage share metadata set', FileService.set_share_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage share exists', ConvenienceFileServiceCommands.share_exists, 'Bool', factory)

# directory commands
cli_storage_data_plane_command(command_table, 'storage directory create', FileService.create_directory, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage directory delete', FileService.delete_directory, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage directory show', FileService.get_directory_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage directory exists', ConvenienceFileServiceCommands.dir_exists, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage directory metadata show', FileService.get_directory_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage directory metadata set', FileService.set_directory_metadata, 'Metadata', factory)

# file commands
cli_storage_data_plane_command(command_table, 'storage file delete', FileService.delete_file, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage file resize', FileService.resize_file, 'Results', factory)
cli_storage_data_plane_command(command_table, 'storage file url', FileService.make_file_url, 'URL', factory)
cli_storage_data_plane_command(command_table, 'storage file generate-sas', FileService.generate_file_shared_access_signature, 'SAS', factory)
cli_storage_data_plane_command(command_table, 'storage file show', FileService.get_file_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage file set', FileService.set_file_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage file exists', ConvenienceFileServiceCommands.file_exists, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage file download', ConvenienceFileServiceCommands.download, 'Results', factory)
cli_storage_data_plane_command(command_table, 'storage file upload', ConvenienceFileServiceCommands.upload, 'Results', factory)
cli_storage_data_plane_command(command_table, 'storage file metadata show', FileService.get_file_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage file metadata set', FileService.set_file_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage file service-properties show', FileService.get_file_service_properties, '[ServiceProperties]', factory)
cli_storage_data_plane_command(command_table, 'storage file service-properties set', FileService.set_file_service_properties, 'ServiceProperties', factory)
cli_storage_data_plane_command(command_table, 'storage file copy start', FileService.copy_file, 'CopyOperationProperties', factory)
cli_storage_data_plane_command(command_table, 'storage file copy cancel', FileService.abort_copy_file, None, factory)
