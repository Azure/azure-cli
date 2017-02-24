# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType)

from azure.cli.core.commands.parameters import \
    (tags_type, get_resource_name_completion_list, enum_choice_list)

from azure.mgmt.datalake.store.models.data_lake_store_account_management_client_enums \
    import(FirewallState,
           TrustedIdProviderState,
           TierType,
           FirewallAllowAzureIpsState)

from azure.mgmt.datalake.store.models import (EncryptionConfigType)

# ARGUMENT DEFINITIONS
# pylint: disable=line-too-long
datalake_store_name_type = CliArgumentType(help='Name of the Data Lake Store account.', options_list=('--account_name',), completer=get_resource_name_completion_list('Microsoft.DataLakeStore/accounts'), id_part=None)

# PARAMETER REGISTRATIONS
register_cli_argument('datalake store', 'account_name', datalake_store_name_type, options_list=('--account', '-n'))
register_cli_argument('datalake store account', 'tags', tags_type)
register_cli_argument('datalake store account', 'tier', help='The desired commitment tier for this account to use.', **enum_choice_list(TierType))
register_cli_argument('datalake store account create', 'encryption_type', help='Indicates what type of encryption to provision the account with. By default, encryption is ServiceManaged. If no encryption is desired, it must be explicitly set with the --disable-encryption flag.', **enum_choice_list(EncryptionConfigType))
register_cli_argument('datalake store account create', 'disable_encryption', help='Indicates that the account will not have any form of encryption applied to it.', action='store_true')
register_cli_argument('datalake store account update', 'trusted_id_provider_state', help='Optionally enable/disable the existing trusted ID providers.', **enum_choice_list(TrustedIdProviderState))
register_cli_argument('datalake store account update', 'firewall_state', help='Optionally enable/disable existing firewall rules.', **enum_choice_list(FirewallState))
register_cli_argument('datalake store account update', 'allow_azure_ips', help='Optionally allow/block Azure originating IPs through the firewall', **enum_choice_list(FirewallAllowAzureIpsState))

# file system params
register_cli_argument('datalake store filesystem', 'path', help='The path in the specified Data Lake Store account where the action should take place. In the format \'/folder/file.txt\', where the first \'/\' after the DNS indicates the root of the file system.')
register_cli_argument('datalake store filesystem create', 'force', help='Indicates that, if the file or folder exists, it should be overwritten', action='store_true')
register_cli_argument('datalake store filesystem create', 'folder', help='Optionally indicates that this new item is a folder and not a file.', action='store_true')
register_cli_argument('datalake store filesystem delete', 'recurse', help='Optionally indicates this should be a recursive delete of the folder.', action='store_true')
register_cli_argument('datalake store filesystem upload', 'overwrite', help='Optionally indicates that, if the destination file or folder exists, it should be overwritten', action='store_true')
register_cli_argument('datalake store filesystem upload', 'thread_count', help='Optionally specify the parallelism of the upload. Default is the number of cores in the local machine.', type=int)
register_cli_argument('datalake store filesystem download', 'overwrite', help='Optionally indicates that, if the destination file or folder exists, it should be overwritten', action='store_true')
register_cli_argument('datalake store filesystem download', 'thread_count', help='Optionally specify the parallelism of the download. Default is the number of cores in the local machine.', type=int)
register_cli_argument('datalake store filesystem preview', 'force', help='Indicates that, if the preview is larger than 1MB, still retrieve it. This can potentially be very slow, depending on how large the file is.', action='store_true')
register_cli_argument('datalake store filesystem join', 'force', help='Indicates that, if the destination file already exists, it should be overwritten', action='store_true')
register_cli_argument('datalake store filesystem join', 'source_paths', help='The list of files in the specified Data Lake Store account to join.', nargs='+')
register_cli_argument('datalake store filesystem move', 'force', help='Indicates that, if the destination file or folder already exists, it should be overwritten and replaced with the file or folder being moved.', action='store_true')
register_cli_argument('datalake store filesystem set-permission', 'permission', help='The octal representation of the permissions for user, group and mask (for example: 777 is full rwx for all entities)', type=int)


