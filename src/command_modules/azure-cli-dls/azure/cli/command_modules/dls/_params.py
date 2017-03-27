# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType)

from azure.cli.core.commands.parameters import \
    (tags_type, get_resource_name_completion_list, resource_group_name_type, enum_choice_list)

from azure.cli.command_modules.dls._validators import validate_resource_group_name
from azure.mgmt.datalake.store.models.data_lake_store_account_management_client_enums \
    import (FirewallState,
            TrustedIdProviderState,
            TierType,
            FirewallAllowAzureIpsState)

from azure.mgmt.datalake.store.models import (EncryptionConfigType)

# ARGUMENT DEFINITIONS
# pylint: disable=line-too-long
datalake_store_name_type = CliArgumentType(help='Name of the Data Lake Store account.', options_list=('--account_name',), completer=get_resource_name_completion_list('Microsoft.DataLakeStore/accounts'), id_part='name')

# PARAMETER REGISTRATIONS
# global params
register_cli_argument('dls', 'account_name', datalake_store_name_type, options_list=('--account', '-n'))
register_cli_argument('dls', 'top', help='Maximum number of items to return.', type=int)
register_cli_argument('dls', 'skip', help='The number of items to skip over before returning elements.', type=int)
register_cli_argument('dls', 'count', help='The Boolean value of true or false to request a count of the matching resources included with the resources in the response, e.g. Categories?$count=true.', type=bool)
# global account params
register_cli_argument('dls account', 'tags', tags_type)
register_cli_argument('dls account', 'resource_group_name', resource_group_name_type, id_part=None, required=False, help='If not specified, will attempt to discover the resource group for the specified Data Lake Store account.', validator=validate_resource_group_name)
# account params
register_cli_argument('dls account show', 'name', datalake_store_name_type, options_list=('--account', '-n'))
register_cli_argument('dls account delete', 'name', datalake_store_name_type, options_list=('--account', '-n'))
register_cli_argument('dls account', 'tier', help='The desired commitment tier for this account to use.', **enum_choice_list(TierType))
register_cli_argument('dls account create', 'resource_group_name', resource_group_name_type, validator=None)
register_cli_argument('dls account create', 'account_name', datalake_store_name_type, options_list=('--account', '-n'), completer=None)
register_cli_argument('dls account create', 'encryption_type', help='Indicates what type of encryption to provision the account with. By default, encryption is ServiceManaged. If no encryption is desired, it must be explicitly set with the --disable-encryption flag.', **enum_choice_list(EncryptionConfigType))
register_cli_argument('dls account create', 'disable_encryption', help='Indicates that the account will not have any form of encryption applied to it.', action='store_true')
register_cli_argument('dls account update', 'trusted_id_provider_state', help='Enable/disable the existing trusted ID providers.', **enum_choice_list(TrustedIdProviderState))
register_cli_argument('dls account update', 'firewall_state', help='Enable/disable existing firewall rules.', **enum_choice_list(FirewallState))
register_cli_argument('dls account update', 'allow_azure_ips', help='Allow/block Azure originating IPs through the firewall', **enum_choice_list(FirewallAllowAzureIpsState))
register_cli_argument('dls account list', 'resource_group_name', resource_group_name_type, validator=None)

# filesystem params
register_cli_argument('dls fs', 'path', help='The path in the specified Data Lake Store account where the action should take place. In the format \'/folder/file.txt\', where the first \'/\' after the DNS indicates the root of the file system.')
register_cli_argument('dls fs create', 'force', help='Indicates that, if the file or folder exists, it should be overwritten', action='store_true')
register_cli_argument('dls fs create', 'folder', help='Indicates that this new item is a folder and not a file.', action='store_true')
register_cli_argument('dls fs delete', 'recurse', help='Indicates this should be a recursive delete of the folder.', action='store_true')
register_cli_argument('dls fs upload', 'overwrite', help='Indicates that, if the destination file or folder exists, it should be overwritten', action='store_true')
register_cli_argument('dls fs upload', 'thread_count', help='Specify the parallelism of the upload. Default is the number of cores in the local machine.', type=int)
register_cli_argument('dls fs download', 'overwrite', help='Indicates that, if the destination file or folder exists, it should be overwritten', action='store_true')
register_cli_argument('dls fs download', 'thread_count', help='Specify the parallelism of the download. Default is the number of cores in the local machine.', type=int)
register_cli_argument('dls fs preview', 'force', help='Indicates that, if the preview is larger than 1MB, still retrieve it. This can potentially be very slow, depending on how large the file is.', action='store_true')
register_cli_argument('dls fs join', 'force', help='Indicates that, if the destination file already exists, it should be overwritten', action='store_true')
register_cli_argument('dls fs join', 'source_paths', help='The list of files in the specified Data Lake Store account to join.', nargs='+')
register_cli_argument('dls fs move', 'force', help='Indicates that, if the destination file or folder already exists, it should be overwritten and replaced with the file or folder being moved.', action='store_true')
register_cli_argument('dls fs set-expiry', 'expiration_time', help='The absolute value of the expiration time expressed as milliseconds since the epoch.')

# filesystem access params
register_cli_argument('dls fs access', 'acl_spec', help=" The ACL specification to set on the path in the format '[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,[default:]user|group|other:[entity id or UPN]:r|-w|-x|-,...'.")
register_cli_argument('dls fs access set-permission', 'permission', help='The octal representation of the permissions for user, group and mask (for example: 777 is full rwx for all entities)', type=int)
register_cli_argument('dls fs access remove-all', 'default_acl', help='A switch that, if specified, indicates that the remove ACL operation should remove the default ACL of the folder. Otherwise the regular ACL is removed.', action='store_true')
