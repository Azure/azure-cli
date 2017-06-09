# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
from argcomplete.completers import FilesCompleter
from six import u as unicode_string

from azure.cli.core._config import az_config
from azure.cli.core.commands.parameters import \
    (ignore_type, tags_type, file_type, get_resource_name_completion_list, enum_choice_list,
     model_choice_list, enum_default, location_type)
from azure.cli.core.commands.validators import get_default_location_from_resource_group
import azure.cli.core.commands.arm  # pylint: disable=unused-import
from azure.cli.core.commands import register_cli_argument, register_extra_cli_argument, CliArgumentType, VersionConstraint

from azure.common import AzureMissingResourceHttpError

from azure.cli.core.profiles import get_sdk, ResourceType

from ._factory import get_storage_data_service_client
from ._validators import \
    (get_datetime_type, get_file_path_validator, validate_metadata,
     get_permission_validator, table_permission_validator, get_permission_help_string,
     resource_type_type, services_type, ipv4_range_type, validate_entity,
     validate_select, validate_source_uri, validate_blob_type, validate_included_datasets,
     validate_custom_domain, validate_public_access,
     process_blob_upload_batch_parameters, process_blob_download_batch_parameters,
     process_file_upload_batch_parameters, process_file_download_batch_parameters,
     get_content_setting_validator, validate_encryption, validate_accept,
     validate_key, storage_account_key_options,
     process_file_download_namespace,
     process_metric_update_namespace, process_blob_copy_batch_namespace,
     get_source_file_or_blob_service_client, process_blob_source_uri,
     get_char_options_validator)


DeleteSnapshot, BlockBlobService, \
    PageBlobService, AppendBlobService = get_sdk(ResourceType.DATA_STORAGE,
                                                 'DeleteSnapshot',
                                                 'BlockBlobService',
                                                 'PageBlobService',
                                                 'AppendBlobService',
                                                 mod='blob')


BlobContentSettings, ContainerPermissions, \
    BlobPermissions, PublicAccess = get_sdk(ResourceType.DATA_STORAGE,
                                            'ContentSettings',
                                            'ContainerPermissions',
                                            'BlobPermissions',
                                            'PublicAccess',
                                            mod='blob.models')

FileContentSettings, SharePermissions, \
    FilePermissions = get_sdk(ResourceType.DATA_STORAGE,
                              'ContentSettings',
                              'SharePermissions',
                              'FilePermissions',
                              mod='file.models')

TableService, TablePayloadFormat = get_sdk(ResourceType.DATA_STORAGE,
                                           'TableService',
                                           'TablePayloadFormat',
                                           mod='table')

AccountPermissions, BaseBlobService, \
    FileService, QueueService, QueuePermissions = get_sdk(ResourceType.DATA_STORAGE,
                                                          'models#AccountPermissions',
                                                          'blob.baseblobservice#BaseBlobService',
                                                          'file#FileService',
                                                          'queue#QueueService',
                                                          'queue.models#QueuePermissions')


# UTILITY

public_access_types = {'off': None, 'blob': PublicAccess.Blob, 'container': PublicAccess.Container}


class CommandContext(object):
    def __init__(self, scope):
        self._scope = scope

    def reg_arg(self, *args, **kwargs):
        return register_cli_argument(self._scope, *args, **kwargs)

    def reg_extra_arg(self, *args, **kwargs):
        return register_extra_cli_argument(self._scope, *args, **kwargs)

    def ignore(self, argument):
        return register_cli_argument(self._scope, argument, ignore_type)

    def arg_group(self, name):
        return ArgumentGroupContext(self._scope, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ArgumentGroupContext(CommandContext):
    def __init__(self, scope, name):
        CommandContext.__init__(self, scope)
        self._name = name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def reg_arg(self, *args, **kwargs):
        kwargs['arg_group'] = self._name
        return CommandContext.reg_arg(self, *args, **kwargs)

    def reg_extra_arg(self, *args, **kwargs):
        kwargs['arg_group'] = self._name
        return CommandContext.reg_extra_arg(self, *args, **kwargs)

# COMPLETERS


def _get_client(service, parsed_args):
    account_name = getattr(parsed_args, 'account_name', None) or az_config.get('storage', 'account', None)
    account_key = getattr(parsed_args, 'account_key', None) or az_config.get('storage', 'key', None)
    connection_string = getattr(parsed_args, 'connection_string', None) or az_config.get('storage', 'connection_string', None)
    sas_token = getattr(parsed_args, 'sas_token', None) or az_config.get('storage', 'sas_token', None)
    return get_storage_data_service_client(
        service, account_name, account_key, connection_string, sas_token)


def get_storage_name_completion_list(service, func, parent=None):
    def completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
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
    def completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
        client = _get_client(service, parsed_args)
        container_name = getattr(parsed_args, container_param)
        return list(getattr(client, func)(container_name))
    return completer


def dir_path_completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
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


def file_path_completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
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


def register_content_settings_argument(scope, settings_class, update, arg_group=None):
    register_cli_argument(scope, 'content_settings', ignore_type, validator=get_content_setting_validator(settings_class, update), arg_group=arg_group)
    register_extra_cli_argument(scope, 'content_type', default=None, help='The content MIME type.', arg_group=arg_group)
    register_extra_cli_argument(scope, 'content_encoding', default=None, help='The content encoding type.', arg_group=arg_group)
    register_extra_cli_argument(scope, 'content_language', default=None, help='The content language.', arg_group=arg_group)
    register_extra_cli_argument(scope, 'content_disposition', default=None, help='Conveys additional information about how to process the response payload, and can also be used to attach additional metadata.', arg_group=arg_group)
    register_extra_cli_argument(scope, 'content_cache_control', default=None, help='The cache control string.', arg_group=arg_group)
    register_extra_cli_argument(scope, 'content_md5', default=None, help='The content\'s MD5 hash.', arg_group=arg_group)


def register_source_uri_arguments(scope):
    register_cli_argument(scope, 'copy_source', options_list=('--source-uri', '-u'), validator=validate_source_uri, required=False, arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_sas', default=None, help='The shared access signature for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_share', default=None, help='The share name for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_path', default=None, help='The file path for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_container', default=None, help='The container name for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_blob', default=None, help='The blob name for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_snapshot', default=None, help='The blob snapshot for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_account_name', default=None, help='The storage account name of the source blob.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_account_key', default=None, help='The storage account key of the source blob.', arg_group='Copy Source')


def register_blob_source_uri_arguments(scope):
    register_cli_argument(scope, 'copy_source', options_list=('--source-uri', '-u'), validator=process_blob_source_uri, required=False, arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_sas', default=None, help='The shared access signature for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_container', default=None, help='The container name for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_blob', default=None, help='The blob name for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_snapshot', default=None, help='The blob snapshot for the source storage account.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_account_name', default=None, help='The storage account name of the source blob.', arg_group='Copy Source')
    register_extra_cli_argument(scope, 'source_account_key', default=None, help='The storage account key of the source blob.', arg_group='Copy Source')


# CUSTOM CHOICE LISTS

blob_types = {'block': BlockBlobService, 'page': PageBlobService, 'append': AppendBlobService}
delete_snapshot_types = {'include': DeleteSnapshot.Include, 'only': DeleteSnapshot.Only}
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
register_cli_argument('storage', 'metadata', nargs='+', help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.', validator=validate_metadata)
register_cli_argument('storage', 'timeout', help='Request timeout in seconds. Applies to each call to the service.', type=int)

register_cli_argument('storage', 'if_modified_since', help='Alter only if modified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')', type=get_datetime_type(False), arg_group='Pre-condition')
register_cli_argument('storage', 'if_unmodified_since', help='Alter only if unmodified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')', type=get_datetime_type(False), arg_group='Pre-condition')
register_cli_argument('storage', 'if_match', arg_group='Pre-condition')
register_cli_argument('storage', 'if_none_match', arg_group='Pre-condition')

register_cli_argument('storage', 'container_name', container_name_type)

for item in ['check-name', 'delete', 'list', 'show', 'show-usage', 'update', 'keys']:
    register_cli_argument('storage account {}'.format(item), 'account_name', account_name_type, options_list=('--name', '-n'))

register_cli_argument('storage account show-connection-string', 'account_name', account_name_type, options_list=('--name', '-n'))
register_cli_argument('storage account show-connection-string', 'protocol', help='The default endpoint protocol.', **enum_choice_list(['http', 'https']))
register_cli_argument('storage account show-connection-string', 'key_name', options_list=('--key',), help='The key to use.', **enum_choice_list(list(storage_account_key_options.keys())))
for item in ['blob', 'file', 'queue', 'table']:
    register_cli_argument('storage account show-connection-string', '{}_endpoint'.format(item), help='Custom endpoint for {}s.'.format(item))

register_cli_argument('storage account create', 'location', location_type, validator=get_default_location_from_resource_group)
register_cli_argument('storage account create', 'account_type', help='The storage account type', **model_choice_list(ResourceType.MGMT_STORAGE, 'AccountType'))

register_cli_argument('storage account create', 'account_name', account_name_type, options_list=('--name', '-n'), completer=None)

register_cli_argument('storage account create', 'kind', help='Indicates the type of storage account.', default=enum_default(ResourceType.MGMT_STORAGE, 'Kind', 'storage'), **model_choice_list(ResourceType.MGMT_STORAGE, 'Kind'))
register_cli_argument('storage account create', 'tags', tags_type)

for item in ['create', 'update']:
    register_cli_argument('storage account {}'.format(item), 'sku', help='The storage account SKU.', **model_choice_list(ResourceType.MGMT_STORAGE, 'SkuName'))
    es_model = get_sdk(ResourceType.MGMT_STORAGE, 'models#EncryptionServices')
    if es_model:
        register_cli_argument('storage account {}'.format(item), 'encryption', nargs='+', help='Specifies which service(s) to encrypt.', validator=validate_encryption, **enum_choice_list(list(es_model._attribute_map.keys())))  # pylint: disable=protected-access

register_cli_argument('storage account create', 'access_tier', help='Required for StandardBlob accounts. The access tier used for billing. Cannot be set for StandardLRS, StandardGRS, StandardRAGRS, or PremiumLRS account types.', **model_choice_list(ResourceType.MGMT_STORAGE, 'AccessTier'))
register_cli_argument('storage account update', 'access_tier', help='The access tier used for billing StandardBlob accounts. Cannot be set for StandardLRS, StandardGRS, StandardRAGRS, or PremiumLRS account types.', **model_choice_list(ResourceType.MGMT_STORAGE, 'AccessTier'))
register_cli_argument('storage account create', 'custom_domain', help='User domain assigned to the storage account. Name is the CNAME source.')
register_cli_argument('storage account update', 'custom_domain', help='User domain assigned to the storage account. Name is the CNAME source. Use "" to clear existing value.', validator=validate_custom_domain)
register_cli_argument('storage account update', 'use_subdomain', help='Specify whether to use indirect CNAME validation.', **enum_choice_list(['true', 'false']))

register_cli_argument('storage account update', 'tags', tags_type, default=None)

register_cli_argument('storage account keys renew', 'key_name', options_list=('--key',), help='The key to regenerate.', validator=validate_key, **enum_choice_list(list(storage_account_key_options.keys())))
register_cli_argument('storage account keys renew', 'account_name', account_name_type, id_part=None)
register_cli_argument('storage account keys list', 'account_name', account_name_type, id_part=None)

register_cli_argument('storage blob', 'blob_name', blob_name_type, options_list=('--name', '-n'))

for item in ['container', 'blob']:
    register_cli_argument('storage {} lease'.format(item), 'lease_duration', type=int)
    register_cli_argument('storage {} lease'.format(item), 'lease_break_period', type=int)

register_cli_argument('storage blob lease', 'blob_name', blob_name_type)

for source in ['destination', 'source']:
    register_cli_argument('storage blob copy', '{}_if_modified_since'.format(source), arg_group='Pre-condition')
    register_cli_argument('storage blob copy', '{}_if_unmodified_since'.format(source), arg_group='Pre-condition')
    register_cli_argument('storage blob copy', '{}_if_match'.format(source), arg_group='Pre-condition')
    register_cli_argument('storage blob copy', '{}_if_none_match'.format(source), arg_group='Pre-condition')
register_cli_argument('storage blob copy', 'container_name', container_name_type, options_list=('--destination-container', '-c'))
register_cli_argument('storage blob copy', 'blob_name', blob_name_type, options_list=('--destination-blob', '-b'), help='Name of the destination blob. If the exists, it will be overwritten.')
register_cli_argument('storage blob copy', 'source_lease_id', arg_group='Copy Source')

# BLOB INCREMENTAL COPY PARAMETERS
register_blob_source_uri_arguments('storage blob incremental-copy start')
register_cli_argument('storage blob incremental-copy start', 'destination_if_modified_since', arg_group='Pre-condition')
register_cli_argument('storage blob incremental-copy start', 'destination_if_unmodified_since', arg_group='Pre-condition')
register_cli_argument('storage blob incremental-copy start', 'destination_if_match', arg_group='Pre-condition')
register_cli_argument('storage blob incremental-copy start', 'destination_if_none_match', arg_group='Pre-condition')
register_cli_argument('storage blob incremental-copy start', 'container_name', container_name_type, options_list=('--destination-container', '-c'))
register_cli_argument('storage blob incremental-copy start', 'blob_name', blob_name_type, options_list=('--destination-blob', '-b'), help='Name of the destination blob. If the exists, it will be overwritten.')
register_cli_argument('storage blob incremental-copy start', 'source_lease_id', arg_group='Copy Source')

register_cli_argument('storage blob delete', 'delete_snapshots', **enum_choice_list(list(delete_snapshot_types.keys())))

register_cli_argument('storage blob exists', 'blob_name', required=True)

with CommandContext('storage blob list') as c:
    c.reg_arg('include',
              help='Specifies additional datasets to include: (c)opy-info, (m)etadata, (s)napshots. Can be combined.',
              validator=validate_included_datasets)
    c.reg_arg('num_results', type=int)

for item in ['download', 'upload']:
    register_cli_argument('storage blob {}'.format(item), 'file_path', options_list=('--file', '-f'), type=file_type, completer=FilesCompleter())
    register_cli_argument('storage blob {}'.format(item), 'max_connections', type=int)
    with VersionConstraint(ResourceType.DATA_STORAGE, min_api='2016-05-31') as c:
        c.register_cli_argument('storage blob {}'.format(item), 'validate_content', action='store_true')

for item in ['update', 'upload', 'upload-batch']:
    register_content_settings_argument('storage blob {}'.format(item), BlobContentSettings, item == 'update')

register_cli_argument('storage blob upload', 'blob_type', help="Defaults to 'page' for *.vhd files, or 'block' otherwise.", options_list=('--type', '-t'), validator=validate_blob_type, **enum_choice_list(blob_types.keys()))
register_cli_argument('storage blob upload', 'maxsize_condition', help='The max length in bytes permitted for an append blob.')
with VersionConstraint(ResourceType.DATA_STORAGE, min_api='2016-05-31') as c:
    c.register_cli_argument('storage blob upload', 'validate_content', help='Specifies that an MD5 hash shall be calculated for each chunk of the blob and verified by the service when the chunk has arrived.')

# TODO: Remove once #807 is complete. Smart Create Generation requires this parameter.
register_extra_cli_argument('storage blob upload', '_subscription_id', options_list=('--subscription',), help=argparse.SUPPRESS)

# BLOB DOWNLOAD-BATCH PARAMETERS
register_cli_argument('storage blob download-batch', 'destination', options_list=('--destination', '-d'))
register_cli_argument('storage blob download-batch', 'source', options_list=('--source', '-s'),
                      validator=process_blob_download_batch_parameters)

register_cli_argument('storage blob download-batch', 'source_container_name', ignore_type)

# BLOB UPLOAD-BATCH PARAMETERS
register_cli_argument('storage blob upload-batch', 'destination', options_list=('--destination', '-d'))
register_cli_argument('storage blob upload-batch', 'source', options_list=('--source', '-s'),
                      validator=process_blob_upload_batch_parameters)

register_cli_argument('storage blob upload-batch', 'source_files', ignore_type)
register_cli_argument('storage blob upload-batch', 'destination_container_name', ignore_type)

register_cli_argument('storage blob upload-batch', 'blob_type',
                      help="Defaults to 'page' for *.vhd files, or 'block' otherwise. The setting will override blob types for every file.",
                      options_list=('--type', '-t'),
                      **enum_choice_list(blob_types.keys()))
register_cli_argument('storage blob upload-batch', 'maxsize_condition',
                      help='The max length in bytes permitted for an append blob.',
                      arg_group='Content Control')
with VersionConstraint(ResourceType.DATA_STORAGE, min_api='2016-05-31') as c:
    c.register_cli_argument('storage blob upload-batch', 'validate_content',
                            help='Specifies that an MD5 hash shall be calculated for each chunk of the blob and verified by' +
                            ' the service when the chunk has arrived.',
                            arg_group='Content Control')
register_cli_argument('storage blob upload-batch', 'lease_id', help='Required if the blob has an active lease')
register_cli_argument('storage blob upload-batch', 'content_encoding', arg_group='Content Control')
register_cli_argument('storage blob upload-batch', 'content_disposition', arg_group='Content Control')
register_cli_argument('storage blob upload-batch', 'content_md5', arg_group='Content Control')
register_cli_argument('storage blob upload-batch', 'content_type', arg_group='Content Control')
register_cli_argument('storage blob upload-batch', 'content_cache_control', arg_group='Content Control')
register_cli_argument('storage blob upload-batch', 'content_language', arg_group='Content Control')
register_cli_argument('storage blob upload-batch', 'max_connections', type=int)

# BLOB COPY-BATCH PARAMETERS

with CommandContext('storage blob copy start-batch') as c:
    c.reg_arg('source_client', ignore_type, validator=get_source_file_or_blob_service_client)

    with c.arg_group('Copy Source') as group:
        group.reg_extra_arg('source_account_name')
        group.reg_extra_arg('source_account_key')
        group.reg_extra_arg('source_uri')
        group.reg_arg('source_sas')
        group.reg_arg('source_container')
        group.reg_arg('source_share')
        group.reg_arg('prefix', validator=process_blob_copy_batch_namespace)

# FILE UPLOAD-BATCH PARAMETERS
with CommandContext('storage file upload-batch') as c:
    c.reg_arg('source', options_list=('--source', '-s'), validator=process_file_upload_batch_parameters)
    c.reg_arg('destination', options_list=('--destination', '-d'))

    with c.arg_group('Download Control') as group:
        group.reg_arg('max_connections')

        with VersionConstraint(ResourceType.DATA_STORAGE, min_api='2016-05-31') as vc:
            vc.register_cli_argument('storage file upload-batch', 'validate_content')

register_content_settings_argument('storage file upload-batch', FileContentSettings,
                                   update=False, arg_group='Content Settings')

# FILE DOWNLOAD-BATCH PARAMETERS
with CommandContext('storage file download-batch') as c:
    c.reg_arg('source', options_list=('--source', '-s'), validator=process_file_download_batch_parameters)
    c.reg_arg('destination', options_list=('--destination', '-d'))

    with c.arg_group('Download Control') as group:
        group.reg_arg('max_connections')

        with VersionConstraint(ResourceType.DATA_STORAGE, min_api='2016-05-31') as vc:
            vc.register_cli_argument('storage file download-batch', 'validate_content')

# FILE COPY-BATCH PARAMETERS
with CommandContext('storage file copy start-batch') as c:
    c.reg_arg('source_client', ignore_type, validator=get_source_file_or_blob_service_client)

    with c.arg_group('Copy Source') as group:
        group.reg_extra_arg('source_account_name')
        group.reg_extra_arg('source_account_key')
        group.reg_extra_arg('source_uri')
        group.reg_arg('source_sas')
        group.reg_arg('source_container')
        group.reg_arg('source_share')

for item in ['file', 'blob']:
    register_cli_argument('storage {} url'.format(item), 'protocol', help='Protocol to use.', default='https', **enum_choice_list(['http', 'https']))
    register_source_uri_arguments('storage {} copy start'.format(item))

register_cli_argument('storage container', 'container_name', container_name_type, options_list=('--name', '-n'))
register_cli_argument('storage container', 'public_access', validator=validate_public_access, help='Specifies whether data in the container may be accessed publically. By default, container data is private ("off") to the account owner. Use "blob" to allow public read access for blobs. Use "container" to allow public read and list access to the entire container.', **enum_choice_list(public_access_types.keys()))

register_cli_argument('storage container create', 'container_name', container_name_type, options_list=('--name', '-n'), completer=None)
register_cli_argument('storage container create', 'fail_on_exist', help='Throw an exception if the container already exists.')

register_cli_argument('storage container delete', 'fail_not_exist', help='Throw an exception if the container does not exist.')

register_cli_argument('storage container exists', 'blob_name', ignore_type)
register_cli_argument('storage container exists', 'snapshot', ignore_type)

register_cli_argument('storage container set-permission', 'signed_identifiers', ignore_type)

register_cli_argument('storage container lease', 'container_name', container_name_type)

register_cli_argument('storage container policy', 'container_name', container_name_type)
register_cli_argument('storage container policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(BaseBlobService, 'container_name', 'get_container_acl'))
for item in ['create', 'delete', 'list', 'show', 'update']:
    register_extra_cli_argument('storage container policy {}'.format(item), 'lease_id', options_list=('--lease-id',), help='The container lease ID.')

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

register_cli_argument('storage file download', 'file_path', options_list=('--dest',), type=file_type, help='Path of the file to write to. The source filename will be used if not specified.', required=False, validator=process_file_download_namespace, completer=FilesCompleter())
register_cli_argument('storage file download', 'path', validator=None)  # validator called manually from process_file_download_namespace so remove the automatic one
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
register_cli_argument('storage file upload', 'local_file_path', options_list=('--source',), type=file_type, completer=FilesCompleter())
register_path_argument('storage file upload', default_file_param='local_file_path')

register_path_argument('storage file url')

for item in ['container', 'share', 'table', 'queue']:
    register_cli_argument('storage {} policy'.format(item), 'start', type=get_datetime_type(True), help='start UTC datetime (Y-m-d\'T\'H:M:S\'Z\'). Defaults to time of request.')
    register_cli_argument('storage {} policy'.format(item), 'expiry', type=get_datetime_type(True), help='expiration UTC datetime in (Y-m-d\'T\'H:M:S\'Z\')')

register_cli_argument('storage table', 'table_name', table_name_type, options_list=('--name', '-n'))

register_cli_argument('storage table batch', 'table_name', table_name_type)

register_cli_argument('storage table create', 'table_name', table_name_type, options_list=('--name', '-n'), completer=None)
register_cli_argument('storage table create', 'fail_on_exist', help='Throw an exception if the table already exists.')

register_cli_argument('storage table policy', 'container_name', table_name_type)
register_cli_argument('storage table policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(TableService, 'container_name', 'get_table_acl'))

register_cli_argument('storage entity', 'entity', options_list=('--entity', '-e'), validator=validate_entity, nargs='+')
register_cli_argument('storage entity', 'property_resolver', ignore_type)
register_cli_argument('storage entity', 'select', nargs='+', help='Space separated list of properties to return for each entity.', validator=validate_select)

register_cli_argument('storage entity insert', 'if_exists', **enum_choice_list(['fail', 'merge', 'replace']))

register_cli_argument('storage entity query', 'accept', help='Specifies how much metadata to include in the response payload.', default='minimal', validator=validate_accept, **enum_choice_list(table_payload_formats.keys()))

register_cli_argument('storage queue', 'queue_name', queue_name_type, options_list=('--name', '-n'))

register_cli_argument('storage queue create', 'queue_name', queue_name_type, options_list=('--name', '-n'), completer=None)

register_cli_argument('storage queue policy', 'container_name', queue_name_type)
register_cli_argument('storage queue policy', 'policy_name', options_list=('--name', '-n'), help='The stored access policy name.', completer=get_storage_acl_name_completion_list(QueueService, 'container_name', 'get_queue_acl'))

register_cli_argument('storage message', 'queue_name', queue_name_type)
register_cli_argument('storage message', 'message_id', options_list=('--id',))
register_cli_argument('storage message', 'content', type=unicode_string, help='Message content, up to 64KB in size.')

for item in ['account', 'blob', 'container', 'file', 'share', 'table', 'queue']:
    register_cli_argument('storage {} generate-sas'.format(item), 'ip', help='Specifies the IP address or range of IP addresses from which to accept requests. Supports only IPv4 style addresses.', type=ipv4_range_type)
    register_cli_argument('storage {} generate-sas'.format(item), 'expiry', help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes invalid. Do not use if a stored access policy is referenced with --id that specifies this value.', type=get_datetime_type(True))
    register_cli_argument('storage {} generate-sas'.format(item), 'start', help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes valid. Do not use if a stored access policy is referenced with --id that specifies this value. Defaults to the time of the request.', type=get_datetime_type(True))
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
register_cli_argument('storage account generate-sas', 'expiry', help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes invalid.', type=get_datetime_type(True))
register_cli_argument('storage account generate-sas', 'start', help='Specifies the UTC datetime (Y-m-d\'T\'H:M\'Z\') at which the SAS becomes valid. Defaults to the time of the request.', type=get_datetime_type(True))
register_cli_argument('storage account generate-sas', 'account_name', account_name_type, options_list=('--account-name',), help='Storage account name. Must be used in conjunction with either storage account key or a SAS token. Environment Variable: AZURE_STORAGE_ACCOUNT')
register_cli_argument('storage account generate-sas', 'sas_token', ignore_type)


#######################################
# storage cors commands parameters
#######################################

with CommandContext('storage cors') as c:
    c.reg_arg('services', validator=get_char_options_validator('bfqt', 'services'))


with CommandContext('storage cors list') as c:
    c.reg_arg('services', validator=get_char_options_validator('bfqt', 'services'), default='bqft', required=False)


with CommandContext('storage cors add') as c:
    c.reg_arg('max_age')
    c.reg_arg('origins', nargs='+')
    c.reg_arg('methods', nargs='+', **enum_choice_list(['DELETE', 'GET', 'HEAD', 'MERGE', 'POST', 'OPTIONS', 'PUT']))
    c.reg_arg('allowed_headers', nargs='+')
    c.reg_arg('exposed_headers', nargs='+')


#######################################
# storage logging commands parameters
#######################################

with CommandContext('storage logging show') as c:
    c.reg_arg('services', validator=get_char_options_validator('bqt', 'services'), required=False, default='bqt',
              help='The storage services from which to retrieve logging info: (b)lob (q)ueue (t)able. Can be combined.')


with CommandContext('storage logging update') as c:
    c.reg_arg('services', validator=get_char_options_validator('bqt', 'services'),
              help='The storage service(s) for which to update logging info: (b)lob (q)ueue (t)able. Can be combined.')
    c.reg_arg('log', validator=get_char_options_validator('rwd', 'log'),
              help='The operations for which to enable logging: (r)ead (w)rite (d)elete. Can be combined.')
    c.reg_arg('retention', type=int, help='Number of days for which to retain logs. 0 to disable.')


#######################################
# storage metrics commands parameters
#######################################

with CommandContext('storage metrics show') as c:
    c.reg_arg('services', validator=get_char_options_validator('bfqt', 'services'), required=False, default='bfqt',
              help='The storage services from which to retrieve metrics info: (b)lob (f)ile (q)ueue (t)able. '
                   'Can be combined.')
    c.reg_arg('interval',
              help='Filter the set of metrics to retrieve by time interval.',
              **enum_choice_list(['hour', 'minute', 'both']))


with CommandContext('storage metrics update') as c:
    c.reg_arg('services', validator=get_char_options_validator('bfqt', 'services'),
              help='The storage service(s) for which to update metrics info: (b)lob (f)ile (q)ueue (t)able. '
                   'Can be combined.')
    c.reg_arg('hour',
              help='Update the hourly metrics.',
              validator=process_metric_update_namespace, **enum_choice_list(['true', 'false']))
    c.reg_arg('minute',
              help='Update the by-minute metrics.', **enum_choice_list(['true', 'false']))
    c.reg_arg('api',
              help='Specify whether to include API in metrics. Applies to both hour and minute metrics if both are '
                   'specified. Must be specified if hour or minute metrics are enabled and being updated.',
              **enum_choice_list(['true', 'false']))
    c.reg_arg('retention',
              type=int, help='Number of days for which to retain metrics. 0 to disable. Applies to both hour and minute'
                             ' metrics if both are specified.')
