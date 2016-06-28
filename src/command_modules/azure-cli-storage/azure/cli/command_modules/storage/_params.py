# pylint: disable=line-too-long
from azure.cli.commands.parameters import (tags_type,
                                           name_type,
                                           get_resource_name_completion_list)
from azure.cli.commands import register_cli_argument, CliArgumentType
from azure.cli.commands.validators import validate_key_value_pairs

from azure.mgmt.storage.models import SkuName

from azure.storage.blob import PublicAccess, BlockBlobService, PageBlobService, AppendBlobService

from ._validators import (
    validate_container_permission, validate_datetime, validate_datetime_as_string, validate_id,
    validate_ip_range, validate_resource_types, validate_services, validate_lease_duration,
    validate_quota)

# PARAMETER CHOICE LISTS

storage_account_key_options = {'primary': 'key1', 'secondary': 'key2'}

# TODO: update this once enums are supported in commands first-class (task #115175885)
storage_account_types = {'Standard_LRS': SkuName.standard_lrs,
                         'Standard_ZRS': SkuName.standard_zrs,
                         'Standard_GRS': SkuName.standard_grs,
                         'Standard_RAGRS': SkuName.standard_ragrs,
                         'Premium_LRS': SkuName.premium_lrs}

# TODO: update this once enums are supported in commands first-class (task #115175885)
public_access_types = {'none': None, 'blob': PublicAccess.Blob, 'container': PublicAccess.Container}

lease_duration_values = {'min':15, 'max':60, 'infinite':-1}
lease_duration_values_string = 'Between {} and {} seconds. ({} for infinite)'.format(
    lease_duration_values['min'],
    lease_duration_values['max'],
    lease_duration_values['infinite'])

blob_types = {'block': BlockBlobService, 'page': PageBlobService, 'append': AppendBlobService}

# PARAMETER TYPE DEFINITIONS
account_name_type = CliArgumentType(
    options_list=('--account-name', '-n'),
    help='the storage account name'
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
    choices=list(blob_types.keys()),
    type=str.lower
)

container_name_type = CliArgumentType(
    options_list=('--container-name', '-c')
)

copy_source_type = CliArgumentType(
    options_list=('--source-uri', '-u')
)

directory_type = CliArgumentType(
    options_list=('--directory-name', '-d')
)

expiry_type = CliArgumentType(
    help='expiration UTC datetime in (Y-m-d\'T\'H:M\'Z\')',
    type=validate_datetime_as_string
)

file_name_type = CliArgumentType(
    options_list=('--file-name', '-f')
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
    choices=list(storage_account_key_options.keys()),
    type=str.lower
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
    options_list=('--id',),
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

policy_name_type = CliArgumentType(
    metavar='NAME',
    help='the stored access policy name'
)

public_access_type = CliArgumentType(
    choices=list(public_access_types.keys()),
    type=str.lower
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

register_cli_argument('storage', 'metadata', metadata_type)
register_cli_argument('storage', 'container_name', container_name_type)
register_cli_argument('storage', 'copy_source', copy_source_type)
register_cli_argument('storage', 'directory_name', directory_type)
register_cli_argument('storage', 'share_name', share_name_type)
register_cli_argument('storage', 'expiry', expiry_type)
register_cli_argument('storage', 'if_modified_since', if_modified_since_type)
register_cli_argument('storage', 'if_unmodified_since', if_unmodified_since_type)
register_cli_argument('storage', 'ip', ip_type)
register_cli_argument('storage', 'lease_break_period', lease_break_period_type)
register_cli_argument('storage', 'lease_duration', lease_duration_type)
register_cli_argument('storage', 'lease_id', lease_id_type)
register_cli_argument('storage', 'permission', permission_type)
register_cli_argument('storage', 'start', start_type)
register_cli_argument('storage', 'timeout', timeout_type)

register_cli_argument('storage account', 'account_name', name_type, help='the storage account name', completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))
register_cli_argument('storage account', 'account_type', account_type_type, options_list=('--type', '-t'))
register_cli_argument('storage account', 'tags', tags_type)
register_cli_argument('storage account set', 'tags', tags_type, default=None)
register_cli_argument('storage account keys', 'key', key_type)

register_cli_argument('storage account connection-string', 'use_http', use_http_type)
register_cli_argument('storage account connection-string', 'account_name', account_name_type, completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))
register_cli_argument('storage account create', 'account_name', completer=None)

register_cli_argument('storage account generate-sas', 'resource_types', resource_types_type)
register_cli_argument('storage account generate-sas', 'services', services_type)

register_cli_argument('storage container', 'container_name', name_type)
register_cli_argument('storage container create', 'public_access', public_access_type)
register_cli_argument('storage container policy', 'policy_name', policy_name_type, options_list=('--policy',))

register_cli_argument('storage blob', 'blob_name', name_type)

register_cli_argument('storage blob copy', 'blob_name', blob_name_type, options_list=('--destination-name', '-n'), help='Name of the destination blob. If the exists, it will be overwritten.')
register_cli_argument('storage blob copy', 'container_name', container_name_type, options_list=('--destination-container', '-c'))

register_cli_argument('storage blob upload', 'blob_type', blob_type_type, options_list=('--type', '-t'))

register_cli_argument('storage share', 'share_name', name_type)
register_cli_argument('storage share', 'quota', quota_type)
register_cli_argument('storage share policy', 'container_name', name_type)
register_cli_argument('storage share policy', 'policy_name', policy_name_type, options_list=('--policy',))

register_cli_argument('storage directory', 'directory_name', name_type)

register_cli_argument('storage file', 'file_name', name_type)
register_cli_argument('storage file', 'directory_name', directory_type, required=False)

register_cli_argument('storage file metadata', 'directory_name', directory_type, required=False)

register_cli_argument('storage file copy', 'directory_name', directory_type, options_list=('--destination-directory', '-d'), required=False, default='')

register_cli_argument('storage file copy', 'file_name', file_name_type, options_list=('--destination-name', '-n'))
register_cli_argument('storage file copy', 'share_name', share_name_type, options_list=('--destination-share', '-s'), help='Name of the destination share. The share must exist.')
