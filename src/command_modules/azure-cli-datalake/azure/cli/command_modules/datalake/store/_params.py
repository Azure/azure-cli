# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType)

from azure.cli.core.commands.parameters import \
    (tags_type, location_type, resource_group_name_type,
     get_resource_name_completion_list, enum_choice_list)

from azure.mgmt.datalake.store.models.data_lake_store_account_management_client_enums \
    import(FirewallState,
           TrustedIdProviderState,
           TierType,
           FirewallAllowAzureIpsState)

from azure.mgmt.datalake.store.models import (EncryptionConfigType)

# ARGUMENT DEFINITIONS
# pylint: disable=line-too-long
datalake_store_name_type = CliArgumentType(help='Name of the Data Lake Analytics account.', options_list=('--account_name',), completer=get_resource_name_completion_list('Microsoft.DataLakeAnalytics/accounts'), id_part=None)

# PARAMETER REGISTRATIONS
register_cli_argument('datalake store', 'account_name', datalake_store_name_type, options_list=('--name', '-n'))
register_cli_argument('datalake store account', 'resource_group_name', resource_group_name_type, completer=None, validator=None)
register_cli_argument('datalake store account create', 'location', location_type)
register_cli_argument('datalake store account create', 'tags', tags_type)
register_cli_argument('datalake store account create', 'tier', help='The desired commitment tier for this account to use.', **enum_choice_list(TierType))
register_cli_argument('datalake store account create', 'encryption_type', help='Indicates what type of encryption to provision the account with. By default, encryption is ServiceManaged. If no encryption is desired, it must be explicitly set with the --disable-encryption flag.', **enum_choice_list(EncryptionConfigType))
register_cli_argument('datalake store account create', 'disable_encryption', help='Indicates that the account will not have any form of encryption applied to it.', action='store_true')
register_cli_argument('datalake store account update', 'tags', tags_type)
register_cli_argument('datalake store account update', 'tier', help='The desired commitment tier for this account to use.', **enum_choice_list(TierType))
register_cli_argument('datalake store account update', 'trusted_id_provider_state', help='Optionally enable/disable the existing trusted ID providers.', **enum_choice_list(TrustedIdProviderState))
register_cli_argument('datalake store account update', 'firewall_state', help='Optionally enable/disable existing firewall rules.', **enum_choice_list(FirewallState))
register_cli_argument('datalake store account update', 'allow_azure_ips', help='Optionally allow/block Azure originating IPs through the firewall', **enum_choice_list(FirewallAllowAzureIpsState))



