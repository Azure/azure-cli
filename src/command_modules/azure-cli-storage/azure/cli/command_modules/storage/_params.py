from os import environ

from azure.cli.commands import COMMON_PARAMETERS as GLOBAL_COMMON_PARAMETERS, patch_aliases
from azure.cli.commands.argument_types import (
    register_cli_argument, register_additional_cli_argument, CliArgumentType
)
from azure.cli.commands._command_creation import get_mgmt_service_client, get_data_service_client
from azure.cli.commands._validators import validate_key_value_pairs, validate_tag, validate_tags
from azure.cli._locale import L

from azure.mgmt.storage import StorageManagementClient, StorageManagementClientConfiguration
from azure.mgmt.storage.models import AccountType

from azure.storage.blob import PublicAccess, BlockBlobService, PageBlobService, AppendBlobService
from azure.storage.file import FileService
from azure.storage import CloudStorageAccount

from ._validators import (
    validate_container_permission, validate_datetime, validate_datetime_as_string, validate_id,
    validate_ip_range, validate_resource_types, validate_services, validate_lease_duration,
    validate_quota)

## PARAMETER CHOICE LISTS

storage_account_key_options = {'primary': 'key1', 'secondary': 'key2'}

# TODO: update this once enums are supported in commands first-class (task #115175885)
storage_account_types = {'Standard_LRS': AccountType.standard_lrs,
                         'Standard_ZRS': AccountType.standard_zrs,
                         'Standard_GRS': AccountType.standard_grs,
                         'Standard_RAGRS': AccountType.standard_ragrs,
                         'Premium_LRS': AccountType.premium_lrs}

# TODO: update this once enums are supported in commands first-class (task #115175885)
public_access_types = {'none': None, 'blob': PublicAccess.Blob, 'container': PublicAccess.Container}

lease_duration_values = {'min':15, 'max':60, 'infinite':-1}
lease_duration_values_string = 'Between {} and {} seconds. ({} for infinite)'.format(
    lease_duration_values['min'],
    lease_duration_values['max'],
    lease_duration_values['infinite'])

blob_types = {'block': BlockBlobService, 'page': PageBlobService, 'append': AppendBlobService}

# PARAMETER TYPE DEFINITIONS

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')

account_name_type = CliArgumentType(
    options_list=('--account-name', '-n'),
    help='the storage account name',
)

account_type_type = CliArgumentType(
    options_list=('--account-type',),
    choices=storage_account_types,
    help='the storage account type'
)

blob_name_type = CliArgumentType(
    options_list=('--blob-name', '-b')
)

blob_type_type = CliArgumentType(
    options_list=('--blob-type',),
    choices=list(blob_types.keys())
)

container_name_type = CliArgumentType(
    options_list=('--container-name', '-c')
)

directory_type = CliArgumentType(
    options_list=('--directory-name','-d')
)

expiry_type = CliArgumentType(
    help='expiration UTC datetime in (Y-m-d\'T\'H:M\'Z\')',
    type=validate_datetime_as_string
)

file_name_type = CliArgumentType(
    options_list=('--file-name','-f')
)


id_type = CliArgumentType(
    help='stored access policy id (up to 64 characters)',
    type=validate_id
)

if_modified_since_type = CliArgumentType(
    help='alter only if modified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')',
    type=validate_datetime
)

if_unmodified_since_type = CliArgumentType(
    help='alter only if unmodified since supplied UTC datetime (Y-m-d\'T\'H:M\'Z\')',
    type=validate_datetime
)

ip_type = CliArgumentType(
    help='specifies the IP address or range of IP addresses from which to accept requests',
    type=validate_ip_range
)

key_type = CliArgumentType(
    help='the key to renew (omit to renew both)',
    choices=list(storage_account_key_options.keys())
)

lease_break_period_type = CliArgumentType(
    metavar='DURATION',
    help='break period. 15-60 seconds or -1 for infinite',
    type=validate_lease_duration
)

lease_duration_type = CliArgumentType(
    metavar='DURATION',
    help='lease duration. 15-60 seconds or -1 for infinite',
    type=validate_lease_duration
)

lease_id_type = CliArgumentType(
    metavar='ID',
    help='lease ID in GUID format'
)

metadata_type = CliArgumentType(
    metavar='METADATA',
    type=validate_key_value_pairs,
    help='metadata in semicolon separated key=value pairs'
)

permission_type = CliArgumentType(
    metavar='PERMISSIONS',
    help='permissions granted: (r)ead (w)rite (d)elete (l)ist. Can be combined',
    type=validate_container_permission
)

public_access_type = CliArgumentType(
    metavar='SPECIFIERS',
    choices=['blob', 'container']
)

quota_type = CliArgumentType(
    type=validate_quota
)

resource_types_type = CliArgumentType(
    type=validate_resource_types,
    help='the resource types the SAS is applicable for. Allowed values: (s)ervice (c)ontainer '
         '(o)bject. Can be combined.'
)

services_type = CliArgumentType(
    type=validate_services,
    help='the storage services the SAS is applicable for. Allowed values: (b)lob (f)ile (q)ueue '
         '(t)able. Can be combined.'
)

share_name_type = CliArgumentType(
    options_list=('--share-name', '-s'),
    help='the name of the file share'
)

signed_identifiers_type = CliArgumentType(
    help='',
    metavar='IDENTIFIERS'
)

start_type = CliArgumentType(
    options_list=('--start',),
    type=validate_datetime_as_string,
    help='start UTC datetime of SAS token (Y-m-d\'T\'H:M\'Z\'). Defaults to time of request.'
)

tags_type = CliArgumentType(
    type=validate_tags,
    help='multiple semicolon separated tags in \'key[=value]\' format'
)

tags_type = CliArgumentType(
    help='a single tag tag in \'key[=value]\' format',
    type=validate_tag
)

timeout_type = CliArgumentType(
    help='timeout in seconds',
    type=int
)

use_http_type = CliArgumentType(
    help='specifies that http should be the default endpoint protocol',
    action='store_const',
    const='http'
)

# PARAMETER SCOPE REGISTRATIONS

register_cli_argument('storage', 'tags', tags_type)
register_cli_argument('storage', 'tag', tags_type)
register_cli_argument('storage', 'metadata', metadata_type)
register_cli_argument('storage', 'blob_name', blob_name_type)
register_cli_argument('storage', 'blob_type', blob_type_type)
register_cli_argument('storage', 'container_name', container_name_type)
register_cli_argument('storage', 'directory_name', directory_type)
register_cli_argument('storage', 'file_name', file_name_type)
register_cli_argument('storage', 'share_name', share_name_type)
register_cli_argument('storage', 'account_name', account_name_type)
register_cli_argument('storage', 'account_type', account_type_type)
register_cli_argument('storage', 'expiry', expiry_type)
register_cli_argument('storage', 'if_modified_since', if_modified_since_type)
register_cli_argument('storage', 'if_unmodified_since', if_unmodified_since_type)
register_cli_argument('storage', 'ip', ip_type)
register_cli_argument('storage', 'lease_break_period', lease_break_period_type)
register_cli_argument('storage', 'lease_duration', lease_duration_type)
register_cli_argument('storage', 'lease_id', lease_id_type)
register_cli_argument('storage', 'permission', permission_type)
register_cli_argument('storage', 'public_access', public_access_type)
register_cli_argument('storage', 'quota', quota_type)
register_cli_argument('storage', 'resource_types', resource_types_type)
register_cli_argument('storage', 'services', services_type)
register_cli_argument('storage', 'signed_identifiers', signed_identifiers_type)
register_cli_argument('storage', 'start', start_type)
register_cli_argument('storage', 'timeout', timeout_type)

register_cli_argument('storage account', 'account_name', account_name_type, options_list=('--name', '-n'))
register_cli_argument('storage account', 'account_type', account_type_type, options_list=('--type', '-t'))

register_cli_argument('storage account keys', 'key', key_type)

register_cli_argument('storage account connection-string', 'use_http', use_http_type)
register_cli_argument('storage account connection-string', 'account_name', account_name_type)

register_cli_argument('storage container', 'container_name', container_name_type)

register_cli_argument('storage blob', 'blob_type', blob_type_type, options_list=('--type', '-t'))

register_cli_argument('storage file', 'directory_name', directory_type, required=False)
register_cli_argument('storage file metadata', 'directory_name', directory_type, required=False)
