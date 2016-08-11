#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
import os

from six import u as unicode_string

from azure.cli.commands.parameters import \
    (tags_type, get_resource_name_completion_list, get_enum_type_completion_list)
from azure.cli.commands import register_cli_argument, register_extra_cli_argument, CliArgumentType
from azure.cli.commands.client_factory import get_data_service_client

from azure.mgmt.storage.models import SkuName, AccessTier, Kind, EncryptionServices
from azure.storage.blob import PublicAccess, DeleteSnapshot, BlockBlobService, PageBlobService, AppendBlobService
from azure.storage.blob.baseblobservice import BaseBlobService
from azure.storage.file import FileService
from azure.storage.table import TableService
from azure.storage.queue import QueueService

from ._validators import \
    (validate_datetime, validate_datetime_as_string, get_file_path_validator, validate_metadata,
     validate_container_permission, validate_resource_types, validate_services, validate_ip_range,
     validate_table_permission, validate_queue_permission, validate_entity, validate_select,
     IgnoreAction)

# CONSTANTS

IGNORE_TYPE = CliArgumentType(help=argparse.SUPPRESS, nargs='?', action=IgnoreAction, required=False)

# COMPLETERS

def _get_client(service, parsed_args):
    account_name = parsed_args.account_name or os.getenv('AZURE_STORAGE_ACCOUNT')
    account_key = parsed_args.account_key or os.getenv('AZURE_STORAGE_KEY')
    connection_string = parsed_args.connection_string or os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    sas_token = parsed_args.sas_token or os.getenv('AZURE_SAS_TOKEN')
    return get_data_service_client(service, account_name, account_key, connection_string, sas_token)

def get_storage_name_completion_list(service, func, parent=None):
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        client = _get_client(service, parsed_args)
        if parent:
            parent_name = getattr(parsed_args, parent)
            method = getattr(client, func)
            items = [x.name for x in method(**{parent: parent_name})]
        else:
            items = [x.name for x in getattr(client, func)()]
        return items
    return completer

def get_storage_acl_name_completion_list(service, container_param, func):
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        client = _get_client(service, parsed_args)
        container_name = getattr(parsed_args, container_param)
        return list(getattr(client, func)(container_name))
    return completer

def entity_completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
    # This is a workaround for the fact that argcomplete always inserts a space after completion
    # In this case, we want the cursor to remain positioned just after the text. We would ideally
    # like it to append the = sign, but argcomplete irritatingly escapes it.
    if prefix in ['RowKey', 'PartitionKey']:
        return []
    return ['RowKey!', 'RowKey*', 'PartitionKey!', 'PartitionKey*']

def file_path_completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
    client = _get_client(FileService, parsed_args)
    share_name = parsed_args.share_name
    directory_name = ''
    if prefix:
        directory_name = prefix
        while directory_name:
            if not client.exists(share_name, directory_name):
                directory_name = os.path.split(directory_name)[0]
            else:
                break
    items = list(client.list_directories_and_files(share_name, directory_name))
    path_format = '{}{}' if directory_name.endswith('/') or not directory_name else '{}/{}'
    names = []
    for i in items:
        name = path_format.format(directory_name, i.name)
        if not hasattr(i.properties, 'content_length'):
            name = '{}/'.format(name)
        names.append(name)
    return names

# PATH REGISTRATION

def register_path_argument(scope, default_file_param=None, options_list=None):
    path_help = 'The path to the file within the file share.'
    if default_file_param:
        path_help = '{} If the file name is omitted, the source file name will be used.'.format(path_help)
    register_extra_cli_argument(scope, 'path', options_list=options_list or ('--path', '-p'), required=default_file_param is None, help=path_help, validator=get_file_path_validator(default_file_param=default_file_param), completer=file_path_completer)
    register_cli_argument(scope, 'file_name', IGNORE_TYPE)
    register_cli_argument(scope, 'directory_name', IGNORE_TYPE)

# CUSTOM CHOICE LISTS

blob_types = {'block': BlockBlobService, 'page': PageBlobService, 'append': AppendBlobService}
public_access_types = {'blob': PublicAccess.Blob, 'container': PublicAccess.Container}
delete_snapshot_types = {'include': DeleteSnapshot.Include, 'only': DeleteSnapshot.Only}
storage_account_key_options = {'both': ['key1', 'key2'], 'primary': ['key1'], 'secondary': ['key2']}

# ARGUMENT TYPES

account_name_type = CliArgumentType(options_list=('--account-name', '-n'), help='The storage account name.', completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'), id_part='name')
blob_name_type = CliArgumentType(options_list=('--blob-name', '-b'), help='The blob name.', completer=get_storage_name_completion_list(BaseBlobService, 'list_blobs', parent='container_name'))
container_name_type = CliArgumentType(options_list=('--container-name', '-c'), help='The container name.', completer=get_storage_name_completion_list(BaseBlobService, 'list_containers'))
directory_type = CliArgumentType(options_list=('--directory-name', '-d'), help='The directory name.', completer=get_storage_name_completion_list(FileService, 'list_directories_and_files', parent='share_name'))
file_name_type = CliArgumentType(options_list=('--file-name', '-f'), completer=get_storage_name_completion_list(FileService, 'list_directories_and_files', parent='share_name'))
share_name_type = CliArgumentType(options_list=('--share-name', '-s'), help='The file share name.', completer=get_storage_name_completion_list(FileService, 'list_shares'))
table_name_type = CliArgumentType(options_list=('--table-name', '-t'), completer=get_storage_name_completion_list(TableService, 'list_tables'))
queue_name_type = CliArgumentType(options_list=('--queue-name', '-q'), help='The queue name.', completer=get_storage_name_completion_list(QueueService, 'list_queues'))

# PARAMETER REGISTRATIONS

register_cli_argument('storage', 'directory_name', directory_type)
register_cli_argument('storage', 'share_name', share_name_type)
register_cli_argument('storage', 'table_name', table_name_type)
register_cli_argument('storage', 'if_modified_since', help='Alter only if modified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')', type=validate_datetime)
register_cli_argument('storage', 'if_unmodified_since', help='Alter only if unmodified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')', type=validate_datetime)
register_cli_argument('storage', 'metadata', nargs='+', help='Metadata in space-separated key=value pairs.', validator=validate_metadata)
register_cli_argument('storage', 'timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)
register_cli_argument('storage', 'container_name', container_name_type)

register_cli_argument('storage', 'content_cache_control', help='The cache control string.')
register_cli_argument('storage', 'content_disposition', help='Conveys additional information about how to process the response payload, and can also be used to attach additional metadata.')
register_cli_argument('storage', 'content_encoding', help='The content encoding type.')
register_cli_argument('storage', 'content_language', help='The content language.')
register_cli_argument('storage', 'content_md5', help='The content\'s MD5 hash.')
register_cli_argument('storage', 'content_type', help='The content MIME type.')

register_cli_argument('storage account', 'account_name', account_name_type, options_list=('--name', '-n'))

register_cli_argument('storage account connection-string', 'account_name', account_name_type, options_list=('--name', '-n'))
register_cli_argument('storage account connection-string', 'protocol', help='The default endpoint protocol.', choices=['http', 'https'], type=str.lower)

register_cli_argument('storage account create', 'account_name', account_name_type, options_list=('--name', '-n'), completer=None)
register_cli_argument('storage account create', 'kind', help='Indicates the type of storage account. (Storage, BlobStorage)', completer=get_enum_type_completion_list(Kind))
register_cli_argument('storage account create', 'tags', tags_type)

for item in ['create', 'update']:
    register_cli_argument('storage account {}'.format(item), 'sku', help='The storage account SKU. (Standard_LRS, Standard_GRS, Standard_RAGRS, Standard_ZRS, Premium_LRS)', completer=get_enum_type_completion_list(SkuName))
    register_cli_argument('storage account {}'.format(item), 'access_tier', help='Required for StandardBlob accounts. The access tier used for billing. Cannot be set for StandardLRS, StandardGRS, StandardRAGRS, or PremiumLRS account types. (Hot, Cool)', completer=get_enum_type_completion_list(AccessTier))
    register_cli_argument('storage account {}'.format(item), 'custom_domain', help='User domain assigned to the storage account. Name is the CNAME source. Use empty string to clear.')
    # TODO: Fix -- encryption does not work
    register_cli_argument('storage account {}'.format(item), 'encryption', help='Provides the encryption settings on the account. If left unspecified the account encryption settings will remain. The default setting is unencrypted.', choices=list(EncryptionServices._attribute_map.keys())) # pylint: disable=protected-access

register_cli_argument('storage account update', 'tags', tags_type, default=None)

register_cli_argument('storage account keys renew', 'key', help='The key(s) to renew.', choices=list(storage_account_key_options.keys()), type=str.lower)

for item in ['container', 'blob']:
    register_cli_argument('storage {} lease'.format(item), 'lease_duration', type=int)
    register_cli_argument('storage {} lease'.format(item), 'lease_break_period', type=int)

register_cli_argument('storage blob', 'blob_name', blob_name_type, options_list=('--name', '-n'))

register_cli_argument('storage blob copy', 'container_name', container_name_type, options_list=('--destination-container', '-c'))
register_cli_argument('storage blob copy', 'blob_name', blob_name_type, options_list=('--destination-blob', '-b'), help='Name of the destination blob. If the exists, it will be overwritten.')

register_cli_argument('storage blob delete', 'delete_snapshots', choices=list(delete_snapshot_types.keys()), type=str.lower)

register_cli_argument('storage blob exists', 'blob_name', required=True)

for item in ['download', 'upload']:
    register_cli_argument('storage blob {}'.format(item), 'file_path', options_list=('--file', '-f'))
    register_cli_argument('storage blob {}'.format(item), 'max_connections', type=int)
    register_cli_argument('storage blob {}'.format(item), 'max_retries', type=int)
    register_cli_argument('storage blob {}'.format(item), 'retry_wait', type=int)
    register_cli_argument('storage blob {}'.format(item), 'validate_content', action='store_true')

register_cli_argument('storage blob upload', 'blob_type', options_list=('--type', '-t'), choices=list(blob_types.keys()), type=str.lower)

register_cli_argument('storage blob url', 'protocol', choices=['http', 'https'], type=str.lower)

for item in ['file', 'blob']:
    register_cli_argument('storage {} copy'.format(item), 'copy_source', options_list=('--source-uri', '-u'))

register_cli_argument('storage container', 'container_name', container_name_type, options_list=('--name', '-n'))

register_cli_argument('storage container create', 'container_name', container_name_type, options_list=('--name', '-n'), completer=None)
register_cli_argument('storage container create', 'fail_on_exist', help='Throw an exception if the container already exists.')
register_cli_argument('storage container create', 'public_access', choices=list(public_access_types.keys()), type=str.lower, help='Specifies whether data in the container may be accessed publically. By default, container data is private to the account owner. Use "blob" to allow public read access for blobs. Use "container" to allow public read and list access to the entire container.')

register_cli_argument('storage container delete', 'fail_not_exist', help='Throw an exception if the container does not exist.')

register_cli_argument('storage container exists', 'blob_name', IGNORE_TYPE)

register_cli_argument('storage container policy', 'container_name', container_name_type)
register_cli_argument('storage container policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(BaseBlobService, 'container_name', 'get_container_acl'))

register_cli_argument('storage share', 'share_name', share_name_type, options_list=('--name', '-n'))

register_cli_argument('storage share exists', 'directory_name', IGNORE_TYPE)
register_cli_argument('storage share exists', 'file_name', IGNORE_TYPE)

register_cli_argument('storage share policy', 'container_name', share_name_type)
register_cli_argument('storage share policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(FileService, 'container_name', 'get_share_acl'))

register_cli_argument('storage directory', 'directory_name', directory_type, options_list=('--name', '-n'))

register_cli_argument('storage directory exists', 'directory_name', required=True)
register_cli_argument('storage directory exists', 'file_name', IGNORE_TYPE)

register_cli_argument('storage file', 'file_name', file_name_type, options_list=('--name', '-n'))
register_cli_argument('storage file', 'directory_name', directory_type, required=False)

register_cli_argument('storage file copy', 'share_name', share_name_type, options_list=('--destination-share', '-s'), help='Name of the destination share. The share must exist.')
register_path_argument('storage file copy start', options_list=('--destination-path', '-p'))
register_path_argument('storage file copy cancel', options_list=('--destination-path', '-p'))

register_path_argument('storage file delete')

register_cli_argument('storage file download', 'file_path', options_list=('--dest',))
register_cli_argument('storage file download', 'progress_callback', IGNORE_TYPE)
register_path_argument('storage file download')

register_cli_argument('storage file exists', 'file_name', required=True)
register_path_argument('storage file exists')

register_path_argument('storage file generate-sas')

register_path_argument('storage file metadata show')
register_path_argument('storage file metadata update')

register_path_argument('storage file resize')

register_path_argument('storage file show')

register_path_argument('storage file update')

register_cli_argument('storage file upload', 'progress_callback', IGNORE_TYPE)
register_cli_argument('storage file upload', 'local_file_path', options_list=('--source',))
register_path_argument('storage file upload', default_file_param='local_file_path')

register_path_argument('storage file url')

for item in ['container', 'share', 'table', 'queue']:
    register_cli_argument('storage {} policy'.format(item), 'start', type=validate_datetime_as_string, help='start UTC datetime (Y-m-d\'T\'H:M\'Z\'). Defaults to time of request.')
    register_cli_argument('storage {} policy'.format(item), 'expiry', type=validate_datetime_as_string, help='expiration UTC datetime in (Y-m-d\'T\'H:M\'Z\')')

for item in ['container', 'share']:
    register_cli_argument('storage {} policy'.format(item), 'permission', options_list=('--permissions',), type=validate_container_permission, help='permissions granted: (r)ead (w)rite (d)elete (l)ist. Can be combined')

register_cli_argument('storage table', 'table_name', table_name_type, options_list=('--name', '-n'))

register_cli_argument('storage table batch', 'table_name', table_name_type)

register_cli_argument('storage table create', 'table_name', table_name_type, options_list=('--name', '-n'), completer=None)
register_cli_argument('storage table create', 'fail_on_exist', help='Throw an exception if the table already exists.')

register_cli_argument('storage table policy', 'container_name', table_name_type)
register_cli_argument('storage table policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(TableService, 'container_name', 'get_table_acl'))
register_cli_argument('storage table policy', 'permission', options_list=('--permissions',), type=validate_table_permission, help='permissions granted: (r)ead (a)dd (u)pdate (d)elete. Can be combined')

register_cli_argument('storage entity', 'entity', options_list=('--entity', '-e'), validator=validate_entity, nargs='+', completer=entity_completer)
register_cli_argument('storage entity', 'property_resolver', IGNORE_TYPE)
register_cli_argument('storage entity', 'select', nargs='+', validator=validate_select)

register_cli_argument('storage entity insert', 'if_exists', choices=['fail', 'merge', 'replace'])

register_cli_argument('storage queue', 'queue_name', queue_name_type, options_list=('--name', '-n'))

register_cli_argument('storage queue create', 'queue_name', queue_name_type, options_list=('--name', '-n'), completer=None)

register_cli_argument('storage queue policy', 'container_name', queue_name_type)
register_cli_argument('storage queue policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(QueueService, 'container_name', 'get_queue_acl'))
register_cli_argument('storage queue policy', 'permission', options_list=('--permissions',), type=validate_queue_permission, help='permissions granted: (r)ead (a)dd (u)pdate (p)rocess [delete]. Can be combined')

register_cli_argument('storage message', 'queue_name', queue_name_type)
register_cli_argument('storage message', 'message_id', options_list=('--id',))
register_cli_argument('storage message', 'content', type=unicode_string)

###################################################################################################

# TODO: Address these in Storage PR3 (week of 8/15/16)
resource_types_type = CliArgumentType(type=validate_resource_types, help='the resource types the SAS is applicable for. Allowed values: (s)ervice (c)ontainer (o)bject. Can be combined.')
register_cli_argument('storage account generate-sas', 'resource_types', resource_types_type)

services_type = CliArgumentType(type=validate_services, help='the storage services the SAS is applicable for. Allowed values: (b)lob (f)ile (q)ueue (t)able. Can be combined.')
register_cli_argument('storage account generate-sas', 'services', services_type)

ip_type = CliArgumentType(help='specifies the IP address or range of IP addresses from which to accept requests', type=validate_ip_range)
register_cli_argument('storage', 'ip', ip_type)
 