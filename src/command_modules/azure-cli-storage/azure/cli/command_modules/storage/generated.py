from __future__ import print_function

from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition

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

# HELPER METHODS

def _patch_aliases(alias_items):
    aliases = PARAMETER_ALIASES.copy()
    aliases.update(alias_items)
    return aliases

# STORAGE ACCOUNT COMMANDS

build_operation(
    'storage account', 'storage_accounts', storage_client_factory,
    [
        AutoCommandDefinition(StorageAccountsOperations.check_name_availability,
                              'Result', 'check-name'),
        AutoCommandDefinition(StorageAccountsOperations.delete, None),
        AutoCommandDefinition(StorageAccountsOperations.get_properties, 'StorageAccount', 'show')
    ], command_table, PARAMETER_ALIASES)

build_operation(
    'storage account', None, cloud_storage_account_service_factory,
    [
        AutoCommandDefinition(CloudStorageAccount.generate_shared_access_signature,
                              'SAS', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage account', None, ConvenienceStorageAccountCommands,
    [
        AutoCommandDefinition(
            ConvenienceStorageAccountCommands.create,
            LongRunningOperation('Creating storage account', 'Storage account created')),
        AutoCommandDefinition(ConvenienceStorageAccountCommands.list, '[StorageAccount]'),
        AutoCommandDefinition(ConvenienceStorageAccountCommands.show_usage, 'Object'),
        AutoCommandDefinition(ConvenienceStorageAccountCommands.set, 'Object'),
        AutoCommandDefinition(ConvenienceStorageAccountCommands.connection_string, 'Object')
    ], command_table, _patch_aliases({
        'account_type': {'name': '--type'}
    }))

build_operation(
    'storage account keys', 'storage_accounts', storage_client_factory,
    [
        AutoCommandDefinition(StorageAccountsOperations.list_keys, '[StorageAccountKeys]', 'list')
    ], command_table, PARAMETER_ALIASES)

build_operation(
    'storage account keys', None, ConvenienceStorageAccountCommands,
    [
        AutoCommandDefinition(ConvenienceStorageAccountCommands.renew_keys, 'Object', 'renew')
    ], command_table, PARAMETER_ALIASES)

# BLOB SERVICE COMMANDS

build_operation(
    'storage container', None, blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.list_containers, '[Container]', 'list'),
        AutoCommandDefinition(BlockBlobService.delete_container, 'Bool', 'delete'),
        AutoCommandDefinition(BlockBlobService.get_container_properties,
                              'ContainerProperties', 'show'),
        AutoCommandDefinition(BlockBlobService.create_container, 'Bool', 'create'),
        AutoCommandDefinition(BlockBlobService.generate_container_shared_access_signature,
                              'SAS', 'generate-sas')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container', None, ConvenienceBlobServiceCommands,
    [
        AutoCommandDefinition(ConvenienceBlobServiceCommands.container_exists, 'Bool', 'exists')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container acl', None, blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.set_container_acl, 'StoredAccessPolicy', 'set'),
        AutoCommandDefinition(BlockBlobService.get_container_acl, '[StoredAccessPolicy]', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container metadata', None, blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.set_container_metadata, 'Properties', 'set'),
        AutoCommandDefinition(BlockBlobService.get_container_metadata, 'Metadata', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage container lease', None, blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.acquire_container_lease, 'LeaseID', 'acquire'),
        AutoCommandDefinition(BlockBlobService.renew_container_lease, 'LeaseID', 'renew'),
        AutoCommandDefinition(BlockBlobService.release_container_lease, None, 'release'),
        AutoCommandDefinition(BlockBlobService.change_container_lease, None, 'change'),
        AutoCommandDefinition(BlockBlobService.break_container_lease, 'Int', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob', None, blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.list_blobs, '[Blob]', 'list'),
        AutoCommandDefinition(BlockBlobService.delete_blob, None, 'delete'),
        AutoCommandDefinition(BlockBlobService.generate_blob_shared_access_signature,
                              'SAS', 'generate-sas'),
        AutoCommandDefinition(BlockBlobService.make_blob_url, 'URL', 'url'),
        AutoCommandDefinition(BlockBlobService.snapshot_blob, 'SnapshotProperties', 'snapshot'),
        AutoCommandDefinition(BlockBlobService.get_blob_properties, 'Properties', 'show'),
        AutoCommandDefinition(BlockBlobService.set_blob_properties, 'Propeties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob', None, ConvenienceBlobServiceCommands,
    [
        AutoCommandDefinition(ConvenienceBlobServiceCommands.blob_exists, 'Bool', 'exists'),
        AutoCommandDefinition(ConvenienceBlobServiceCommands.download, 'Object'),
        AutoCommandDefinition(ConvenienceBlobServiceCommands.upload, 'Object')
    ], command_table, _patch_aliases({
        'blob_type': {'name': '--type'}
    }), STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob service-properties', None, blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.get_blob_service_properties,
                              '[ServiceProperties]', 'show'),
        AutoCommandDefinition(BlockBlobService.set_blob_service_properties,
                              'ServiceProperties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob metadata', None, blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.get_blob_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(BlockBlobService.set_blob_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob lease', None, blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.acquire_blob_lease, 'LeaseID', 'acquire'),
        AutoCommandDefinition(BlockBlobService.renew_blob_lease, 'LeaseID', 'renew'),
        AutoCommandDefinition(BlockBlobService.release_blob_lease, None, 'release'),
        AutoCommandDefinition(BlockBlobService.change_blob_lease, None, 'change'),
        AutoCommandDefinition(BlockBlobService.break_blob_lease, 'Int', 'break')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage blob copy', None, blob_data_service_factory,
    [
        AutoCommandDefinition(BlockBlobService.copy_blob, 'CopyOperationProperties', 'start'),
        AutoCommandDefinition(BlockBlobService.abort_copy_blob, None, 'cancel'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

# FILE SERVICE COMMANDS

build_operation(
    'storage share', None, file_data_service_factory,
    [
        AutoCommandDefinition(FileService.list_shares, '[Share]', 'list'),
        AutoCommandDefinition(FileService.list_directories_and_files,
                              '[ShareContents]', 'contents'),
        AutoCommandDefinition(FileService.create_share, 'Boolean', 'create'),
        AutoCommandDefinition(FileService.delete_share, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.generate_share_shared_access_signature,
                              'SAS', 'generate-sas'),
        AutoCommandDefinition(FileService.get_share_stats, 'ShareStats', 'stats'),
        AutoCommandDefinition(FileService.get_share_properties, 'Properties', 'show'),
        AutoCommandDefinition(FileService.set_share_properties, 'Properties', 'set')

    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share', None, ConvenienceFileServiceCommands,
    [
        AutoCommandDefinition(ConvenienceFileServiceCommands.share_exists, 'Boolean', 'exists')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share metadata', None, file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_share_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(FileService.set_share_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage share acl', None, file_data_service_factory,
    [
        AutoCommandDefinition(FileService.set_share_acl, '[StoredAccessPolicy]', 'set'),
        AutoCommandDefinition(FileService.get_share_acl, 'StoredAccessPolicy', 'show'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory', None, file_data_service_factory,
    [
        AutoCommandDefinition(FileService.create_directory, 'Boolean', 'create'),
        AutoCommandDefinition(FileService.delete_directory, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.get_directory_properties, 'Properties', 'show')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory', None, ConvenienceFileServiceCommands,
    [
        AutoCommandDefinition(ConvenienceFileServiceCommands.dir_exists, 'Bool', 'exists')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage directory metadata', None, file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_directory_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(FileService.set_directory_metadata, 'Metadata', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file', None, file_data_service_factory,
    [
        AutoCommandDefinition(FileService.delete_file, 'Boolean', 'delete'),
        AutoCommandDefinition(FileService.resize_file, 'Result', 'resize'),
        AutoCommandDefinition(FileService.make_file_url, 'URL', 'url'),
        AutoCommandDefinition(FileService.generate_file_shared_access_signature,
                              'SAS', 'generate-sas'),
        AutoCommandDefinition(FileService.get_file_properties, 'Properties', 'show'),
        AutoCommandDefinition(FileService.set_file_properties, 'Properties', 'set')
    ], command_table, _patch_aliases({
        'directory_name': {'required': False}
    }), STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file', None, ConvenienceFileServiceCommands,
    [
        AutoCommandDefinition(ConvenienceFileServiceCommands.file_exists, 'Bool', 'exists'),
        AutoCommandDefinition(ConvenienceFileServiceCommands.download, 'Object'),
        AutoCommandDefinition(ConvenienceFileServiceCommands.upload, 'Object')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file metadata', None, file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_file_metadata, 'Metadata', 'show'),
        AutoCommandDefinition(FileService.set_file_metadata, 'Metadata', 'set')
    ], command_table, _patch_aliases({
        'directory_name': {'required': False}
    }), STORAGE_DATA_CLIENT_ARGS)


build_operation(
    'storage file service-properties', None, file_data_service_factory,
    [
        AutoCommandDefinition(FileService.get_file_service_properties, 'ServiceProperties', 'show'),
        AutoCommandDefinition(FileService.set_file_service_properties, 'ServiceProperties', 'set')
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)

build_operation(
    'storage file copy', None, file_data_service_factory,
    [
        AutoCommandDefinition(FileService.copy_file, 'CopyOperationPropeties', 'start'),
        AutoCommandDefinition(FileService.abort_copy_file, None, 'cancel'),
    ], command_table, PARAMETER_ALIASES, STORAGE_DATA_CLIENT_ARGS)
