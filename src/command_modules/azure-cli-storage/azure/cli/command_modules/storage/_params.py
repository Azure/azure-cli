#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from six import u as unicode_string

from azure.cli.core._config import az_config
from azure.cli.core.commands.parameters import \
    (ignore_type, tags_type, get_resource_name_completion_list, get_enum_type_completion_list)
import azure.cli.core.commands.arm # pylint: disable=unused-import
from azure.cli.core.commands import register_cli_argument, register_extra_cli_argument, CliArgumentType
from azure.cli.core.commands.client_factory import get_data_service_client

from azure.common import AzureMissingResourceHttpError
from azure.mgmt.storage.models import SkuName, AccessTier, Kind, EncryptionServices
from azure.storage.models import AccountPermissions
from azure.storage.blob import PublicAccess, DeleteSnapshot, BlockBlobService, PageBlobService, AppendBlobService
from azure.storage.blob.baseblobservice import BaseBlobService
from azure.storage.blob.models import ContentSettings as BlobContentSettings, ContainerPermissions, BlobPermissions
from azure.storage.file import FileService
from azure.storage.file.models import ContentSettings as FileContentSettings, SharePermissions, FilePermissions
from azure.storage.table import TableService, TablePayloadFormat
from azure.storage.queue import QueueService
from azure.storage.queue.models import QueuePermissions

from ._validators import \
    (datetime_type, datetime_string_type, get_file_path_validator, validate_metadata,
     get_permission_validator, table_permission_validator, get_permission_help_string,
     resource_type_type, services_type, ipv4_range_type, validate_entity,
     validate_select, validate_source_uri,
     get_content_setting_validator, validate_encryption, validate_accept,
     process_file_download_namespace, process_logging_update_namespace,
     process_metric_update_namespace)

# COMPLETERS

def _get_client(service, parsed_args):
    account_name = parsed_args.account_name or az_config.get('storage', 'account', None)
    account_key = parsed_args.account_key or az_config.get('storage', 'key', None)
    connection_string = parsed_args.connection_string or az_config.get('storage', 'connection_string', None)
    sas_token = parsed_args.sas_token or az_config.get('storage', 'sas_token', None)
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

def dir_path_completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
    client = _get_client(FileService, parsed_args)
    share_name = parsed_args.share_name
    directory_name = prefix or ''
    try:
        items = list(client.list_directories_and_files(share_name, directory_name))
    except AzureMissingResourceHttpError:
        directory_name = directory_name.rsplit('/', 1)[0] if '/' in directory_name else ''
        items = list(client.list_directories_and_files(share_name, directory_name))

    dir_list = [x for x in items if not hasattr(x.properties, 'content_length')]
    path_format = '{}{}/' if directory_name.endswith('/') or not directory_name else '{}/{}/'
    names = []
    for d in dir_list:
        name = path_format.format(directory_name, d.name)
        names.append(name)
    return sorted(names)

def file_path_completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
    client = _get_client(FileService, parsed_args)
    share_name = parsed_args.share_name
    directory_name = prefix or ''
    try:
        items = list(client.list_directories_and_files(share_name, directory_name))
    except AzureMissingResourceHttpError:
        directory_name = directory_name.rsplit('/', 1)[0] if '/' in directory_name else ''
        items = list(client.list_directories_and_files(share_name, directory_name))

    path_format = '{}{}' if directory_name.endswith('/') or not directory_name else '{}/{}'
    names = []
    for i in items:
        name = path_format.format(directory_name, i.name)
        if not hasattr(i.properties, 'content_length'):
            name = '{}/'.format(name)
        names.append(name)
    return sorted(names)

# PATH REGISTRATION

def register_path_argument(scope, default_file_param=None, options_list=None):
    path_help = 'The path to the file within the file share.'
    if default_file_param:
        path_help = '{} If the file name is omitted, the source file name will be used.'.format(path_help)
    register_extra_cli_argument(scope, 'path', options_list=options_list or ('--path', '-p'), required=default_file_param is None, help=path_help, validator=get_file_path_validator(default_file_param=default_file_param), completer=file_path_completer)
    register_cli_argument(scope, 'file_name', ignore_type)
    register_cli_argument(scope, 'directory_name', ignore_type)

# EXTRA PARAMETER SET REGISTRATION

def register_content_settings_argument(scope, settings_class, update):
    register_cli_argument(scope, 'content_settings', ignore_type, validator=get_content_setting_validator(settings_class, update))
    register_extra_cli_argument(scope, 'content_type', default=None, help='The content MIME type.')
    register_extra_cli_argument(scope, 'content_encoding', default=None, help='The content encoding type.')
    register_extra_cli_argument(scope, 'content_language', default=None, help='The content language.')
    register_extra_cli_argument(scope, 'content_disposition', default=None, help='Conveys additional information about how to process the response payload, and can also be used to attach additional metadata.')
    register_extra_cli_argument(scope, 'content_cache_control', default=None, help='The cache control string.')
    register_extra_cli_argument(scope, 'content_md5', default=None, help='The content\'s MD5 hash.')

def register_source_uri_arguments(scope):
    register_cli_argument(scope, 'copy_source', options_list=('--source-uri', '-u'), validator=validate_source_uri, required=False)
    register_extra_cli_argument(scope, 'source_sas', default=None, help='The shared access signature for the source storage account.')
    register_extra_cli_argument(scope, 'source_share', default=None, help='The share name for the source storage account.')
    register_extra_cli_argument(scope, 'source_path', default=None, help='The file path for the source storage account.')
    register_extra_cli_argument(scope, 'source_container', default=None, help='The container name for the source storage account.')
    register_extra_cli_argument(scope, 'source_blob', default=None, help='The blob name for the source storage account.')
    register_extra_cli_argument(scope, 'source_snapshot', default=None, help='The blob snapshot for the source storage account.')


# CUSTOM CHOICE LISTS

blob_types = {'block': BlockBlobService, 'page': PageBlobService, 'append': AppendBlobService}
public_access_types = {'blob': PublicAccess.Blob, 'container': PublicAccess.Container}
delete_snapshot_types = {'include': DeleteSnapshot.Include, 'only': DeleteSnapshot.Only}
storage_account_key_options = {'both': ['key1', 'key2'], 'primary': ['key1'], 'secondary': ['key2']}
table_payload_formats = {'none': TablePayloadFormat.JSON_NO_METADATA, 'minimal': TablePayloadFormat.JSON_MINIMAL_METADATA, 'full': TablePayloadFormat.JSON_FULL_METADATA}

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
register_cli_argument('storage', 'retry_wait', options_list=('--retry-interval',))
register_cli_argument('storage', 'progress_callback', ignore_type)
register_cli_argument('storage', 'if_modified_since', help='Alter only if modified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')', type=datetime_type)
register_cli_argument('storage', 'if_unmodified_since', help='Alter only if unmodified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')', type=datetime_type)
register_cli_argument('storage', 'metadata', nargs='+', help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.', validator=validate_metadata)
register_cli_argument('storage', 'timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)
register_cli_argument('storage', 'container_name', container_name_type)

for item in ['check-name', 'delete', 'list', 'show', 'show-usage', 'update', 'keys']:
    register_cli_argument('storage account {}'.format(item), 'account_name', account_name_type, options_list=('--name', '-n'))

register_cli_argument('storage account connection-string', 'account_name', account_name_type, options_list=('--name', '-n'))
register_cli_argument('storage account connection-string', 'protocol', help='The default endpoint protocol.', choices=['http', 'https'], type=str.lower)

register_cli_argument('storage account create', 'account_name', account_name_type, options_list=('--name', '-n'), completer=None)

register_cli_argument('storage account create', 'kind', help='Indicates the type of storage account. (Storage, BlobStorage)', completer=get_enum_type_completion_list(Kind))
register_cli_argument('storage account create', 'tags', tags_type)

for item in ['create', 'update']:
    register_cli_argument('storage account {}'.format(item), 'sku', help='The storage account SKU. (Standard_LRS, Standard_GRS, Standard_RAGRS, Standard_ZRS, Premium_LRS)', completer=get_enum_type_completion_list(SkuName))
    register_cli_argument('storage account {}'.format(item), 'access_tier', help='Required for StandardBlob accounts. The access tier used for billing. Cannot be set for StandardLRS, StandardGRS, StandardRAGRS, or PremiumLRS account types. (Hot, Cool)', completer=get_enum_type_completion_list(AccessTier))
    register_cli_argument('storage account {}'.format(item), 'encryption', nargs='+', help='Specifies which service(s) to encrypt.', choices=list(EncryptionServices._attribute_map.keys()), validator=validate_encryption) # pylint: disable=protected-access

register_cli_argument('storage account create', 'custom_domain', help='User domain assigned to the storage account. Name is the CNAME source.')
register_cli_argument('storage account update', 'custom_domain', help='User domain assigned to the storage account. Name is the CNAME source. Use "" to clear existing value.')

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

for item in ['update', 'upload']:
    register_content_settings_argument('storage blob {}'.format(item), BlobContentSettings, item == 'update')

register_cli_argument('storage blob upload', 'blob_type', options_list=('--type', '-t'), choices=list(blob_types.keys()), type=str.lower)
register_cli_argument('storage blob upload', 'maxsize_condition', help='The max length in bytes permitted for an append blob.')
register_cli_argument('storage blob upload', 'validate_content', help='Specifies that an MD5 hash shall be calculated for each chunk of the blob and verified by the service when the chunk has arrived.')

for item in ['file', 'blob']:
    register_cli_argument('storage {} url'.format(item), 'protocol', help='Protocol to use.', choices=['http', 'https'], default='https', type=str.lower)
    register_source_uri_arguments('storage {} copy start'.format(item))

register_cli_argument('storage container', 'container_name', container_name_type, options_list=('--name', '-n'))

register_cli_argument('storage container create', 'container_name', container_name_type, options_list=('--name', '-n'), completer=None)
register_cli_argument('storage container create', 'fail_on_exist', help='Throw an exception if the container already exists.')
register_cli_argument('storage container create', 'public_access', choices=list(public_access_types.keys()), type=str.lower, help='Specifies whether data in the container may be accessed publically. By default, container data is private to the account owner. Use "blob" to allow public read access for blobs. Use "container" to allow public read and list access to the entire container.')

register_cli_argument('storage container delete', 'fail_not_exist', help='Throw an exception if the container does not exist.')

register_cli_argument('storage container exists', 'blob_name', ignore_type)
register_cli_argument('storage container exists', 'blob_name', ignore_type)
register_cli_argument('storage container exists', 'snapshot', ignore_type)

register_cli_argument('storage container policy', 'container_name', container_name_type)
register_cli_argument('storage container policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(BaseBlobService, 'container_name', 'get_container_acl'))

register_cli_argument('storage share', 'share_name', share_name_type, options_list=('--name', '-n'))

register_cli_argument('storage share exists', 'directory_name', ignore_type)
register_cli_argument('storage share exists', 'file_name', ignore_type)

register_cli_argument('storage share policy', 'container_name', share_name_type)
register_cli_argument('storage share policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(FileService, 'container_name', 'get_share_acl'))

register_cli_argument('storage directory', 'directory_name', directory_type, options_list=('--name', '-n'))

register_cli_argument('storage directory exists', 'directory_name', required=True)
register_cli_argument('storage directory exists', 'file_name', ignore_type)

register_cli_argument('storage file', 'file_name', file_name_type, options_list=('--name', '-n'))
register_cli_argument('storage file', 'directory_name', directory_type, required=False)

register_cli_argument('storage file copy', 'share_name', share_name_type, options_list=('--destination-share', '-s'), help='Name of the destination share. The share must exist.')
register_path_argument('storage file copy start', options_list=('--destination-path', '-p'))
register_path_argument('storage file copy cancel', options_list=('--destination-path', '-p'))

register_path_argument('storage file delete')

register_cli_argument('storage file download', 'file_path', options_list=('--dest',), help='Path of the file to write to. The source filename will be used if not specified.', required=False, validator=process_file_download_namespace)
register_cli_argument('storage file download', 'path', validator=None) # validator called manually from process_file_download_namespace so remove the automatic one
register_cli_argument('storage file download', 'progress_callback', ignore_type)
register_path_argument('storage file download')

register_cli_argument('storage file exists', 'file_name', required=True)
register_path_argument('storage file exists')

register_path_argument('storage file generate-sas')

register_cli_argument('storage file list', 'directory_name', options_list=('--path', '-p'), help='The directory path within the file share.', completer=dir_path_completer)

register_path_argument('storage file metadata show')
register_path_argument('storage file metadata update')

register_cli_argument('storage file resize', 'content_length', options_list=('--size',))
register_path_argument('storage file resize')

register_path_argument('storage file show')

for item in ['update', 'upload']:
    register_content_settings_argument('storage file {}'.format(item), FileContentSettings, item == 'update')

register_path_argument('storage file update')

register_cli_argument('storage file upload', 'progress_callback', ignore_type)
register_cli_argument('storage file upload', 'local_file_path', options_list=('--source',))
register_path_argument('storage file upload', default_file_param='local_file_path')

register_path_argument('storage file url')

for item in ['container', 'share', 'table', 'queue']:
    register_cli_argument('storage {} policy'.format(item), 'start', type=datetime_string_type, help='start UTC datetime (Y-m-d\'T\'H:M\'Z\'). Defaults to time of request.')
    register_cli_argument('storage {} policy'.format(item), 'expiry', type=datetime_string_type, help='expiration UTC datetime in (Y-m-d\'T\'H:M\'Z\')')

register_cli_argument('storage table', 'table_name', table_name_type, options_list=('--name', '-n'))

register_cli_argument('storage table batch', 'table_name', table_name_type)

register_cli_argument('storage table create', 'table_name', table_name_type, options_list=('--name', '-n'), completer=None)
register_cli_argument('storage table create', 'fail_on_exist', help='Throw an exception if the table already exists.')

register_cli_argument('storage table policy', 'container_name', table_name_type)
register_cli_argument('storage table policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(TableService, 'container_name', 'get_table_acl'))

register_cli_argument('storage entity', 'entity', options_list=('--entity', '-e'), validator=validate_entity, nargs='+')
register_cli_argument('storage entity', 'property_resolver', ignore_type)
register_cli_argument('storage entity', 'select', nargs='+', help='Space separated list of properties to return for each entity.', validator=validate_select)

register_cli_argument('storage entity insert', 'if_exists', choices=['fail', 'merge', 'replace'])

register_cli_argument('storage entity query', 'accept', help='Specifies how much metadata to include in the response payload.', choices=table_payload_formats.keys(), default='minimal', validator=validate_accept)

register_cli_argument('storage queue', 'queue_name', queue_name_type, options_list=('--name', '-n'))

register_cli_argument('storage queue create', 'queue_name', queue_name_type, options_list=('--name', '-n'), completer=None)

register_cli_argument('storage queue policy', 'container_name', queue_name_type)
register_cli_argument('storage queue policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(QueueService, 'container_name', 'get_queue_acl'))

register_cli_argument('storage message', 'queue_name', queue_name_type)
register_cli_argument('storage message', 'message_id', options_list=('--id',))
register_cli_argument('storage message', 'content', type=unicode_string, help='Message content, up to 64KB in size.')

for item in ['account', 'blob', 'container', 'file', 'share', 'table', 'queue']:
    register_cli_argument('storage {} generate-sas'.format(item), 'ip', help='Specifies the IP address or range of IP addresses from which to accept requests. Supports only IPv4 style addresses.', type=ipv4_range_type)
    register_cli_argument('storage {} generate-sas'.format(item), 'expiry', help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes invalid. Do not use if a stored access policy is referenced with --id that specifies this value.', type=datetime_string_type)
    register_cli_argument('storage {} generate-sas'.format(item), 'start', help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes valid. Do not use if a stored access policy is referenced with --id that specifies this value. Defaults to the time of the request.', type=datetime_string_type)
    register_cli_argument('storage {} generate-sas'.format(item), 'protocol', options_list=('--https-only',), help='Only permit requests made with the HTTPS protocol. If omitted, requests from both the HTTP and HTTPS protocol are permitted.', action='store_const', const='https')

help_format = 'The permissions the SAS grants. Allowed values: {}. Do not use if a stored access policy is referenced with --id that specifies this value. Can be combined.'
policies = [
    {'name': 'account', 'container': '', 'class': '', 'sas_perm_help': 'The permissions the SAS grants. Allowed values: {}. Can be combined.'.format(get_permission_help_string(AccountPermissions)), 'policy_perm_help': '', 'perm_validator': get_permission_validator(AccountPermissions)},
    {'name': 'container', 'container': 'container', 'class': BaseBlobService, 'sas_perm_help': help_format.format(get_permission_help_string(ContainerPermissions)), 'policy_perm_help': 'Allowed values: {}. Can be combined.'.format(get_permission_help_string(ContainerPermissions)), 'perm_validator': get_permission_validator(ContainerPermissions)},
    {'name': 'blob', 'container': 'container', 'class': BaseBlobService, 'sas_perm_help': help_format.format(get_permission_help_string(BlobPermissions)), 'policy_perm_help': '', 'perm_validator': get_permission_validator(BlobPermissions)},
    {'name': 'share', 'container': 'share', 'class': FileService, 'sas_perm_help': help_format.format(get_permission_help_string(SharePermissions)), 'policy_perm_help': 'Allowed values: {}. Can be combined.'.format(get_permission_help_string(SharePermissions)), 'perm_validator': get_permission_validator(SharePermissions)},
    {'name': 'file', 'container': 'share', 'class': FileService, 'sas_perm_help': help_format.format(get_permission_help_string(FilePermissions)), 'policy_perm_help': '', 'perm_validator': get_permission_validator(FilePermissions)},
    {'name': 'table', 'container': 'table', 'class': TableService, 'sas_perm_help': help_format.format('(r)ead/query (a)dd (u)pdate (d)elete'), 'policy_perm_help': 'Allowed values: {}. Can be combined.'.format('(r)ead/query (a)dd (u)pdate (d)elete'), 'perm_validator': table_permission_validator},
    {'name': 'queue', 'container': 'queue', 'class': QueueService, 'sas_perm_help': help_format.format(get_permission_help_string(QueuePermissions)), 'policy_perm_help': 'Allowed values: {}. Can be combined.'.format(get_permission_help_string(QueuePermissions)), 'perm_validator': get_permission_validator(QueuePermissions)}
]
for item in policies:
    register_cli_argument('storage {} generate-sas'.format(item['name']), 'id', options_list=('--policy-name',), help='The name of a stored access policy within the {}\'s ACL.'.format(item['container']), completer=get_storage_acl_name_completion_list(item['class'], '{}_name'.format(item['container']), 'get_{}_acl'.format(item['container'])))
    register_cli_argument('storage {} generate-sas'.format(item['name']), 'permission', options_list=('--permissions',), help=item['sas_perm_help'], validator=item['perm_validator'])
    register_cli_argument('storage {} policy'.format(item['name']), 'permission', options_list=('--permissions',), help=item['policy_perm_help'], validator=item['perm_validator'])

register_cli_argument('storage account generate-sas', 'services', help='The storage services the SAS is applicable for. Allowed values: (b)lob (f)ile (q)ueue (t)able. Can be combined.', type=services_type)
register_cli_argument('storage account generate-sas', 'resource_types', help='The resource types the SAS is applicable for. Allowed values: (s)ervice (c)ontainer (o)bject. Can be combined.', type=resource_type_type)
register_cli_argument('storage account generate-sas', 'expiry', help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes invalid.', type=datetime_string_type)
register_cli_argument('storage account generate-sas', 'start', help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes valid. Defaults to the time of the request.', type=datetime_string_type)
register_cli_argument('storage account generate-sas', 'account_name', account_name_type, options_list=('--account-name',), help='Storage account name. Must be used in conjunction with either storage account key or a SAS token. Var: AZURE_STORAGE_ACCOUNT')

register_cli_argument('storage logging show', 'services', help='The storage services from which to retrieve logging info: (b)lob (q)ueue (t)able. Can be combined.')

register_cli_argument('storage logging update', 'services', help='The storage service(s) for which to update logging info: (b)lob (q)ueue (t)able. Can be combined.', validator=process_logging_update_namespace)
register_cli_argument('storage logging update', 'log', help='The operations for which to enable logging: (r)ead (w)rite (d)elete. Can be combined.')
register_cli_argument('storage logging update', 'retention', type=int, help='Number of days for which to retain logs. 0 to disable.')

register_cli_argument('storage metrics show', 'services', help='The storage services from which to retrieve metrics info: (b)lob (f)ile (q)ueue (t)able. Can be combined.')
register_cli_argument('storage metrics show', 'interval', help='Filter the set of metrics to retrieve by time interval.', choices=['hour', 'minute', 'both'])

register_cli_argument('storage metrics update', 'services', help='The storage service(s) for which to update metrics info: (b)lob (f)ile (q)ueue (t)able. Can be combined.')
register_cli_argument('storage metrics update', 'hour', help='Update the hourly metrics.', choices=['enable', 'disable'], validator=process_metric_update_namespace)
register_cli_argument('storage metrics update', 'minute', help='Update the by-minute metrics.', choices=['enable', 'disable'])
register_cli_argument('storage metrics update', 'api', help='Specify whether to include API in metrics. Applies to both hour and minute metrics if both are specified. Must be specified if hour or minute metrics are enabled and being updated.', choices=['enable', 'disable'])
register_cli_argument('storage metrics update', 'retention', type=int, help='Number of days for which to retain metrics. 0 to disable. Applies to both hour and minute metrics if both are specified.')

register_cli_argument('storage cors', 'max_age', type=int, help='The number of seconds the client/browser should cache a preflight response.', default="0")
register_cli_argument('storage cors', 'origins', nargs='+', help='List of origin domains that will be allowed via CORS, or "*" to allow all domains.')
register_cli_argument('storage cors', 'methods', nargs='+', help='List of HTTP methods allowed to be executed by the origin.', choices=['DELETE', 'GET', 'HEAD', 'MERGE', 'POST', 'OPTIONS', 'PUT'], type=str.upper)
register_cli_argument('storage cors', 'allowed_headers', nargs='+', help='List of response headers allowed to be part of the cross-origin request.')
register_cli_argument('storage cors', 'exposed_headers', nargs='+', help='List of response headers to expose to CORS clients.')

register_cli_argument('storage cors add', 'services', help='The storage service(s) for which to add the CORS rule: (b)lob (f)ile (q)ueue (t)able. Can be combined.')

register_cli_argument('storage cors clear', 'services', help='The storage service(s) for which to clear CORS rules: (b)lob (f)ile (q)ueue (t)able. Can be combined.')

register_cli_argument('storage cors list', 'services', help='The storage service(s) for which to list the CORS rules: (b)lob (f)ile (q)ueue (t)able. Can be combined.')
