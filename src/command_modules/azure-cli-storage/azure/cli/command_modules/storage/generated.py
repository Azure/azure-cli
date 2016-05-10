from __future__ import print_function

from azure.cli.commands import CommandTable, patch_aliases
from azure.cli.commands._auto_command import build_operation, CommandDefinition

from azure.mgmt.storage.operations import StorageAccountsOperations
from azure.storage.blob import BlockBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount

from ._params import (PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS, storage_client_factory,
                      blob_data_service_factory, file_data_service_factory,
                      cloud_storage_account_service_factory)
from .custom import (ConvenienceStorageAccountCommands, ConvenienceBlobServiceCommands,
                     ConvenienceFileServiceCommands)

command_table = CommandTable()

# STORAGE ACCOUNT COMMANDS

build_operation(
    'storage account', 'storage_accounts', storage_client_factory,
    [
        CommandDefinition(StorageAccountsOperations.check_name_availability,
                          'Result', 'check-name'),
        CommandDefinition(StorageAccountsOperations.delete, None),
        CommandDefinition(StorageAccountsOperations.get_properties, 'StorageAccount', 'show')
    ], command_table, PARAMETER_ALIASES)

build_operation(
    'storage account', None, cloud_storage_account_service_factory,
    [
        CommandDefinition(CloudStorageAccount.generate_shared_access_signature,
                          'SAS', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage account', None, ConvenienceStorageAccountCommands,
    [
        CommandDefinition(ConvenienceStorageAccountCommands.create, 'Result'),
        CommandDefinition(ConvenienceStorageAccountCommands.list, '[StorageAccount]'),
        CommandDefinition(ConvenienceStorageAccountCommands.show_usage, 'Object'),
        CommandDefinition(ConvenienceStorageAccountCommands.set, 'Object'),
        CommandDefinition(ConvenienceStorageAccountCommands.connection_string, 'Object')
    ], command_table, patch_aliases(PARAMETER_ALIASES, {
        'account_type': {'name': '--type'}
    }))

build_operation(
    'storage account keys', 'storage_accounts', storage_client_factory,
    [
        CommandDefinition(StorageAccountsOperations.list_keys, '[StorageAccountKeys]', 'list')
    ], command_table, PARAMETER_ALIASES)

build_operation(
    'storage account keys', None, ConvenienceStorageAccountCommands,
    [
        CommandDefinition(ConvenienceStorageAccountCommands.renew_keys, 'Object', 'renew')
    ], command_table, PARAMETER_ALIASES)

# BLOB SERVICE COMMANDS

build_operation(
    'storage container', None, blob_data_service_factory,
    [
        CommandDefinition(BlockBlobService.list_containers, '[Container]', 'list'),
        CommandDefinition(BlockBlobService.delete_container, 'Bool', 'delete'),
        CommandDefinition(BlockBlobService.get_container_properties,
                          'ContainerProperties', 'show'),
        CommandDefinition(BlockBlobService.create_container, 'Bool', 'create'),
        CommandDefinition(BlockBlobService.generate_container_shared_access_signature,
                          'SAS', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container', None, ConvenienceBlobServiceCommands,
    [
        CommandDefinition(ConvenienceBlobServiceCommands.container_exists, 'Bool', 'exists')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container acl', None, blob_data_service_factory,
    [
        CommandDefinition(BlockBlobService.set_container_acl, 'StoredAccessPolicy', 'set'),
        CommandDefinition(BlockBlobService.get_container_acl, '[StoredAccessPolicy]', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container metadata', None, blob_data_service_factory,
    [
        CommandDefinition(BlockBlobService.set_container_metadata, 'Properties', 'set'),
        CommandDefinition(BlockBlobService.get_container_metadata, 'Metadata', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container lease', None, blob_data_service_factory,
    [
        CommandDefinition(BlockBlobService.acquire_container_lease, 'LeaseID', 'acquire'),
        CommandDefinition(BlockBlobService.renew_container_lease, 'LeaseID', 'renew'),
        CommandDefinition(BlockBlobService.release_container_lease, None, 'release'),
        CommandDefinition(BlockBlobService.change_container_lease, None, 'change'),
        CommandDefinition(BlockBlobService.break_container_lease, 'Int', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob', None, blob_data_service_factory,
    [
        CommandDefinition(BlockBlobService.list_blobs, '[Blob]', 'list'),
        CommandDefinition(BlockBlobService.delete_blob, None, 'delete'),
        CommandDefinition(BlockBlobService.generate_blob_shared_access_signature,
                          'SAS', 'generate-sas'),
        CommandDefinition(BlockBlobService.make_blob_url, 'URL', 'url'),
        CommandDefinition(BlockBlobService.snapshot_blob, 'SnapshotProperties', 'snapshot'),
        CommandDefinition(BlockBlobService.get_blob_properties, 'Properties', 'show'),
        CommandDefinition(BlockBlobService.set_blob_properties, 'Propeties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob', None, ConvenienceBlobServiceCommands,
    [
        CommandDefinition(ConvenienceBlobServiceCommands.blob_exists, 'Bool', 'exists'),
        CommandDefinition(ConvenienceBlobServiceCommands.download, 'Object'),
        CommandDefinition(ConvenienceBlobServiceCommands.upload, 'Object')
    ], command_table, patch_aliases(PARAMETER_ALIASES, {
        'blob_type': {'name': '--type'}
    }), STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob service-properties', None, blob_data_service_factory,
    [
        CommandDefinition(BlockBlobService.get_blob_service_properties,
                          '[ServiceProperties]', 'show'),
        CommandDefinition(BlockBlobService.set_blob_service_properties,
                          'ServiceProperties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob metadata', None, blob_data_service_factory,
    [
        CommandDefinition(BlockBlobService.get_blob_metadata, 'Metadata', 'show'),
        CommandDefinition(BlockBlobService.set_blob_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob lease', None, blob_data_service_factory,
    [
        CommandDefinition(BlockBlobService.acquire_blob_lease, 'LeaseID', 'acquire'),
        CommandDefinition(BlockBlobService.renew_blob_lease, 'LeaseID', 'renew'),
        CommandDefinition(BlockBlobService.release_blob_lease, None, 'release'),
        CommandDefinition(BlockBlobService.change_blob_lease, None, 'change'),
        CommandDefinition(BlockBlobService.break_blob_lease, 'Int', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob copy', None, blob_data_service_factory,
    [
        CommandDefinition(BlockBlobService.copy_blob, 'CopyOperationProperties', 'start'),
        CommandDefinition(BlockBlobService.abort_copy_blob, None, 'cancel'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

# FILE SERVICE COMMANDS

build_operation(
    'storage share', None, file_data_service_factory,
    [
        CommandDefinition(FileService.list_shares, '[Share]', 'list'),
        CommandDefinition(FileService.list_directories_and_files,
                          '[ShareContents]', 'contents'),
        CommandDefinition(FileService.create_share, 'Boolean', 'create'),
        CommandDefinition(FileService.delete_share, 'Boolean', 'delete'),
        CommandDefinition(FileService.generate_share_shared_access_signature,
                          'SAS', 'generate-sas'),
        CommandDefinition(FileService.get_share_stats, 'ShareStats', 'stats'),
        CommandDefinition(FileService.get_share_properties, 'Properties', 'show'),
        CommandDefinition(FileService.set_share_properties, 'Properties', 'set')

    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share', None, ConvenienceFileServiceCommands,
    [
        CommandDefinition(ConvenienceFileServiceCommands.share_exists, 'Boolean', 'exists')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share metadata', None, file_data_service_factory,
    [
        CommandDefinition(FileService.get_share_metadata, 'Metadata', 'show'),
        CommandDefinition(FileService.set_share_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share acl', None, file_data_service_factory,
    [
        CommandDefinition(FileService.set_share_acl, '[StoredAccessPolicy]', 'set'),
        CommandDefinition(FileService.get_share_acl, 'StoredAccessPolicy', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory', None, file_data_service_factory,
    [
        CommandDefinition(FileService.create_directory, 'Boolean', 'create'),
        CommandDefinition(FileService.delete_directory, 'Boolean', 'delete'),
        CommandDefinition(FileService.get_directory_properties, 'Properties', 'show')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory', None, ConvenienceFileServiceCommands,
    [
        CommandDefinition(ConvenienceFileServiceCommands.dir_exists, 'Bool', 'exists')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory metadata', None, file_data_service_factory,
    [
        CommandDefinition(FileService.get_directory_metadata, 'Metadata', 'show'),
        CommandDefinition(FileService.set_directory_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file', None, file_data_service_factory,
    [
        CommandDefinition(FileService.delete_file, 'Boolean', 'delete'),
        CommandDefinition(FileService.resize_file, 'Result', 'resize'),
        CommandDefinition(FileService.make_file_url, 'URL', 'url'),
        CommandDefinition(FileService.generate_file_shared_access_signature,
                          'SAS', 'generate-sas'),
        CommandDefinition(FileService.get_file_properties, 'Properties', 'show'),
        CommandDefinition(FileService.set_file_properties, 'Properties', 'set')
    ], command_table, patch_aliases(PARAMETER_ALIASES, {
        'directory_name': {'required': False}
    }), STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file', None, ConvenienceFileServiceCommands,
    [
        CommandDefinition(ConvenienceFileServiceCommands.file_exists, 'Bool', 'exists'),
        CommandDefinition(ConvenienceFileServiceCommands.download, 'Object'),
        CommandDefinition(ConvenienceFileServiceCommands.upload, 'Object')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file metadata', None, file_data_service_factory,
    [
        CommandDefinition(FileService.get_file_metadata, 'Metadata', 'show'),
        CommandDefinition(FileService.set_file_metadata, 'Metadata', 'set')
    ], command_table, patch_aliases(PARAMETER_ALIASES, {
        'directory_name': {'required': False}
    }), STORAGE_DATA_CLIENT_ARGS)


build_operation(
    'storage file service-properties', None, file_data_service_factory,
    [
        CommandDefinition(FileService.get_file_service_properties, 'ServiceProperties', 'show'),
        CommandDefinition(FileService.set_file_service_properties, 'ServiceProperties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file copy', None, file_data_service_factory,
    [
        CommandDefinition(FileService.copy_file, 'CopyOperationPropeties', 'start'),
        CommandDefinition(FileService.abort_copy_file, None, 'cancel'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)
