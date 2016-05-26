from __future__ import print_function

from azure.cli.commands import CommandTable
from azure.cli.commands.command_types import cli_command

from azure.mgmt.storage.operations import StorageAccountsOperations
from azure.storage.blob import BlockBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount

from azure.cli.command_modules.storage._command_type import cli_storage_data_plane_command
from azure.cli.command_modules.storage._factory import \
    (storage_client_factory, blob_data_service_factory, file_data_service_factory,
                      cloud_storage_account_service_factory)
from azure.cli.command_modules.storage.custom import *

command_table = CommandTable()

# storage account commands
factory = lambda kwargs: storage_client_factory().storage_accounts
cli_command(command_table, 'storage account check-name', StorageAccountsOperations.check_name_availability, 'Result', factory)
cli_command(command_table, 'storage account delete', StorageAccountsOperations.delete, None, factory)
cli_command(command_table, 'storage account show', StorageAccountsOperations.get_properties, 'StorageAccount', factory)
cli_command(command_table, 'storage account keys list', StorageAccountsOperations.list_keys, '[StorageAccountKeys]', factory)
cli_command(command_table, 'storage account create', create_storage_account, 'Result')
cli_command(command_table, 'storage account list', list_storage_accounts, '[StorageAccount]')
cli_command(command_table, 'storage account show-usage', show_storage_account_usage, 'Result')
cli_command(command_table, 'storage account set', set_storage_account_properties, 'Result')
cli_command(command_table, 'storage account connection-string', show_storage_account_connection_string, 'Result')
cli_command(command_table, 'storage account keys renew', renew_storage_account_keys, '[StorageAccountKeys]')
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
cli_storage_data_plane_command(command_table, 'storage container exists', container_exists, 'Bool', factory)

# blob commands
cli_storage_data_plane_command(command_table, 'storage blob list', BlockBlobService.list_blobs, '[Blob]', factory)
cli_storage_data_plane_command(command_table, 'storage blob delete', BlockBlobService.delete_blob, None, factory)
cli_storage_data_plane_command(command_table, 'storage blob generate-sas', BlockBlobService.generate_blob_shared_access_signature, 'SAS', factory)
cli_storage_data_plane_command(command_table, 'storage blob url', BlockBlobService.make_blob_url, 'URL', factory)
cli_storage_data_plane_command(command_table, 'storage blob snapshot', BlockBlobService.snapshot_blob, 'SnapshotProperties', factory)
cli_storage_data_plane_command(command_table, 'storage blob show', BlockBlobService.get_blob_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage blob set', BlockBlobService.set_blob_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage blob exists', blob_exists, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage blob download', download_blob, 'Results', factory)
cli_storage_data_plane_command(command_table, 'storage blob upload', upload_blob, 'Results', factory)
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
cli_storage_data_plane_command(command_table, 'storage share exists', share_exists, 'Bool', factory)

# directory commands
cli_storage_data_plane_command(command_table, 'storage directory create', FileService.create_directory, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage directory delete', FileService.delete_directory, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage directory show', FileService.get_directory_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage directory exists', dir_exists, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage directory metadata show', FileService.get_directory_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage directory metadata set', FileService.set_directory_metadata, 'Metadata', factory)

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
    ], command_table, patch_aliases(PARAMETER_ALIASES, {
        'blob_name': {
            'name': '--destination-name -n',
            'help': 'Name of the destination blob. If the blob exists, it will be overwritten.'
        },
        'container_name': {
            'name': '--destination-container -c'
        },
        'copy_source': {
            'name': '--source-uri -u'
        }
    }), patch_aliases(STORAGE_DATA_CLIENT_ARGS, {
        'account_name': {'name': '--account-name'}
    }))

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
    ], command_table, patch_aliases(PARAMETER_ALIASES, {
        'directory_name': {
            'name': '--destination-directory -d',
            'required': False,
            'default': ''
        },
        'file_name': {
            'name': '--destination-name -n',
        },
        'share_name': {
            'name': '--destination-share -s',
            'help': 'Name of the destination share. The share must exist.'
        },
        'copy_source': {
            'name': '--source-uri -u'
        }
    }), patch_aliases(STORAGE_DATA_CLIENT_ARGS, {
        'account_name': {'name': '--account-name'}
    }))
# file commands
cli_storage_data_plane_command(command_table, 'storage file delete', FileService.delete_file, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage file resize', FileService.resize_file, 'Results', factory)
cli_storage_data_plane_command(command_table, 'storage file url', FileService.make_file_url, 'URL', factory)
cli_storage_data_plane_command(command_table, 'storage file generate-sas', FileService.generate_file_shared_access_signature, 'SAS', factory)
cli_storage_data_plane_command(command_table, 'storage file show', FileService.get_file_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage file set', FileService.set_file_properties, 'Properties', factory)
cli_storage_data_plane_command(command_table, 'storage file exists', file_exists, 'Bool', factory)
cli_storage_data_plane_command(command_table, 'storage file download', download_file, 'Results', factory)
cli_storage_data_plane_command(command_table, 'storage file upload', upload_file, 'Results', factory)
cli_storage_data_plane_command(command_table, 'storage file metadata show', FileService.get_file_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage file metadata set', FileService.set_file_metadata, 'Metadata', factory)
cli_storage_data_plane_command(command_table, 'storage file service-properties show', FileService.get_file_service_properties, '[ServiceProperties]', factory)
cli_storage_data_plane_command(command_table, 'storage file service-properties set', FileService.set_file_service_properties, 'ServiceProperties', factory)
cli_storage_data_plane_command(command_table, 'storage file copy start', FileService.copy_file, 'CopyOperationProperties', factory)
cli_storage_data_plane_command(command_table, 'storage file copy cancel', FileService.abort_copy_file, None, factory)
