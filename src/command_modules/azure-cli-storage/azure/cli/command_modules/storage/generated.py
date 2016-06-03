# pylint: disable=line-too-long
from __future__ import print_function

from azure.mgmt.storage.operations import StorageAccountsOperations
from azure.storage.blob import BlockBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount

from azure.cli.commands import CommandTable
from azure.cli.commands.command_types import cli_command
from azure.cli.command_modules.storage._command_type import cli_storage_data_plane_command
from azure.cli.command_modules.storage._factory import \
    (storage_client_factory, blob_data_service_factory, file_data_service_factory,
     cloud_storage_account_service_factory)
from azure.cli.command_modules.storage.custom import \
    (create_storage_account, list_storage_accounts, show_storage_account_usage,
     set_storage_account_properties, show_storage_account_connection_string,
     renew_storage_account_keys, container_exists, blob_exists, download_blob, upload_blob,
     share_exists, dir_exists, file_exists, upload_file, download_file)

command_table = CommandTable()

# storage account commands
factory = lambda kwargs: storage_client_factory().storage_accounts
cli_command(command_table, 'storage account check-name', StorageAccountsOperations.check_name_availability, factory)
cli_command(command_table, 'storage account delete', StorageAccountsOperations.delete, factory)
cli_command(command_table, 'storage account show', StorageAccountsOperations.get_properties, factory)
cli_command(command_table, 'storage account create', create_storage_account)
cli_command(command_table, 'storage account list', list_storage_accounts)
cli_command(command_table, 'storage account show-usage', show_storage_account_usage)
cli_command(command_table, 'storage account set', set_storage_account_properties)
cli_command(command_table, 'storage account connection-string', show_storage_account_connection_string)
cli_command(command_table, 'storage account keys renew', renew_storage_account_keys)
cli_command(command_table, 'storage account keys list', StorageAccountsOperations.list_keys, factory)
cli_storage_data_plane_command(command_table, 'storage account generate-sas', CloudStorageAccount.generate_shared_access_signature, cloud_storage_account_service_factory)

# container commands
factory = blob_data_service_factory
cli_storage_data_plane_command(command_table, 'storage container list', BlockBlobService.list_containers, factory)
cli_storage_data_plane_command(command_table, 'storage container delete', BlockBlobService.delete_container, factory)
cli_storage_data_plane_command(command_table, 'storage container show', BlockBlobService.get_container_properties, factory)
cli_storage_data_plane_command(command_table, 'storage container create', BlockBlobService.create_container, factory)
cli_storage_data_plane_command(command_table, 'storage container generate-sas', BlockBlobService.generate_container_shared_access_signature, factory)
cli_storage_data_plane_command(command_table, 'storage container metadata set', BlockBlobService.set_container_metadata, factory)
cli_storage_data_plane_command(command_table, 'storage container metadata show', BlockBlobService.get_container_metadata, factory)
cli_storage_data_plane_command(command_table, 'storage container lease acquire', BlockBlobService.acquire_container_lease, factory)
cli_storage_data_plane_command(command_table, 'storage container lease renew', BlockBlobService.renew_container_lease, factory)
cli_storage_data_plane_command(command_table, 'storage container lease release', BlockBlobService.release_container_lease, factory)
cli_storage_data_plane_command(command_table, 'storage container lease change', BlockBlobService.change_container_lease, factory)
cli_storage_data_plane_command(command_table, 'storage container lease break', BlockBlobService.break_container_lease, factory)
cli_storage_data_plane_command(command_table, 'storage container exists', container_exists, factory)

# blob commands
cli_storage_data_plane_command(command_table, 'storage blob list', BlockBlobService.list_blobs, factory)
cli_storage_data_plane_command(command_table, 'storage blob delete', BlockBlobService.delete_blob, factory)
cli_storage_data_plane_command(command_table, 'storage blob generate-sas', BlockBlobService.generate_blob_shared_access_signature, factory)
cli_storage_data_plane_command(command_table, 'storage blob url', BlockBlobService.make_blob_url, factory)
cli_storage_data_plane_command(command_table, 'storage blob snapshot', BlockBlobService.snapshot_blob, factory)
cli_storage_data_plane_command(command_table, 'storage blob show', BlockBlobService.get_blob_properties, factory)
cli_storage_data_plane_command(command_table, 'storage blob set', BlockBlobService.set_blob_properties, factory)
cli_storage_data_plane_command(command_table, 'storage blob exists', blob_exists, factory)
cli_storage_data_plane_command(command_table, 'storage blob download', download_blob, factory)
cli_storage_data_plane_command(command_table, 'storage blob upload', upload_blob, factory)
cli_storage_data_plane_command(command_table, 'storage blob service-properties show', BlockBlobService.get_blob_service_properties, factory)
cli_storage_data_plane_command(command_table, 'storage blob service-properties set', BlockBlobService.set_blob_service_properties, factory)
cli_storage_data_plane_command(command_table, 'storage blob metadata show', BlockBlobService.get_blob_metadata, factory)
cli_storage_data_plane_command(command_table, 'storage blob metadata set', BlockBlobService.set_blob_metadata, factory)
cli_storage_data_plane_command(command_table, 'storage blob lease acquire', BlockBlobService.acquire_blob_lease, factory)
cli_storage_data_plane_command(command_table, 'storage blob lease renew', BlockBlobService.renew_blob_lease, factory)
cli_storage_data_plane_command(command_table, 'storage blob lease release', BlockBlobService.release_blob_lease, factory)
cli_storage_data_plane_command(command_table, 'storage blob lease change', BlockBlobService.change_blob_lease, factory)
cli_storage_data_plane_command(command_table, 'storage blob lease break', BlockBlobService.break_blob_lease, factory)
cli_storage_data_plane_command(command_table, 'storage blob copy start', BlockBlobService.copy_blob, factory)
cli_storage_data_plane_command(command_table, 'storage blob copy cancel', BlockBlobService.abort_copy_blob, factory)

# share commands
factory = file_data_service_factory
cli_storage_data_plane_command(command_table, 'storage share list', FileService.list_shares, factory)
cli_storage_data_plane_command(command_table, 'storage share contents', FileService.list_directories_and_files, factory)
cli_storage_data_plane_command(command_table, 'storage share create', FileService.create_share, factory)
cli_storage_data_plane_command(command_table, 'storage share delete', FileService.delete_share, factory)
cli_storage_data_plane_command(command_table, 'storage share generate-sas', FileService.generate_share_shared_access_signature, factory)
cli_storage_data_plane_command(command_table, 'storage share stats', FileService.get_share_stats, factory)
cli_storage_data_plane_command(command_table, 'storage share show', FileService.get_share_properties, factory)
cli_storage_data_plane_command(command_table, 'storage share set', FileService.set_share_properties, factory)
cli_storage_data_plane_command(command_table, 'storage share metadata show', FileService.get_share_metadata, factory)
cli_storage_data_plane_command(command_table, 'storage share metadata set', FileService.set_share_metadata, factory)
cli_storage_data_plane_command(command_table, 'storage share exists', share_exists, factory)

# directory commands
cli_storage_data_plane_command(command_table, 'storage directory create', FileService.create_directory, factory)
cli_storage_data_plane_command(command_table, 'storage directory delete', FileService.delete_directory, factory)
cli_storage_data_plane_command(command_table, 'storage directory show', FileService.get_directory_properties, factory)
cli_storage_data_plane_command(command_table, 'storage directory exists', dir_exists, factory)
cli_storage_data_plane_command(command_table, 'storage directory metadata show', FileService.get_directory_metadata, factory)
cli_storage_data_plane_command(command_table, 'storage directory metadata set', FileService.set_directory_metadata, factory)

# file commands
cli_storage_data_plane_command(command_table, 'storage file delete', FileService.delete_file, factory)
cli_storage_data_plane_command(command_table, 'storage file resize', FileService.resize_file, factory)
cli_storage_data_plane_command(command_table, 'storage file url', FileService.make_file_url, factory)
cli_storage_data_plane_command(command_table, 'storage file generate-sas', FileService.generate_file_shared_access_signature, factory)
cli_storage_data_plane_command(command_table, 'storage file show', FileService.get_file_properties, factory)
cli_storage_data_plane_command(command_table, 'storage file set', FileService.set_file_properties, factory)
cli_storage_data_plane_command(command_table, 'storage file exists', file_exists, factory)
cli_storage_data_plane_command(command_table, 'storage file download', download_file, factory)
cli_storage_data_plane_command(command_table, 'storage file upload', upload_file, factory)
cli_storage_data_plane_command(command_table, 'storage file metadata show', FileService.get_file_metadata, factory)
cli_storage_data_plane_command(command_table, 'storage file metadata set', FileService.set_file_metadata, factory)
cli_storage_data_plane_command(command_table, 'storage file service-properties show', FileService.get_file_service_properties, factory)
cli_storage_data_plane_command(command_table, 'storage file service-properties set', FileService.set_file_service_properties, factory)
cli_storage_data_plane_command(command_table, 'storage file copy start', FileService.copy_file, factory)
cli_storage_data_plane_command(command_table, 'storage file copy cancel', FileService.abort_copy_file, factory)
