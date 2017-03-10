# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from argcomplete.completers import FilesCompleter
from azure.cli.core.commands import \
    (register_cli_argument, CliArgumentType)
from azure.cli.core.commands.parameters import \
    (tags_type,
     get_resource_name_completion_list,
     resource_group_name_type,
     enum_choice_list)

from azure.cli.command_modules.datalake.analytics._validators import validate_resource_group_name

# pylint: disable=line-too-long
from azure.mgmt.datalake.analytics.account.models.data_lake_analytics_account_management_client_enums \
    import(FirewallState,
           TierType,
           FirewallAllowAzureIpsState)

from azure.mgmt.datalake.analytics.job.models.data_lake_analytics_job_management_client_enums \
    import(CompileMode)


# ARGUMENT DEFINITIONS
# pylint: disable=line-too-long
datalake_analytics_name_type = CliArgumentType(help='Name of the Data Lake Analytics account.', options_list=('--account_name',), completer=get_resource_name_completion_list('Microsoft.DataLakeAnalytics/accounts'), id_part='name')

# PARAMETER REGISTRATIONS
# account params
register_cli_argument('datalake analytics', 'resource_group_name', resource_group_name_type, id_part=None, required=False, help='If not specified, will attempt to discover the resource group for the specified Data Lake Analytics account.', validator=validate_resource_group_name)
register_cli_argument('datalake analytics', 'account_name', datalake_analytics_name_type, options_list=('--account', '-n'))
register_cli_argument('datalake analytics account', 'tags', tags_type)
register_cli_argument('datalake analytics account', 'tier', help='The desired commitment tier for this account to use.', **enum_choice_list(TierType))
register_cli_argument('datalake analytics account create', 'resource_group_name', resource_group_name_type, validator=None)
register_cli_argument('datalake analytics account create', 'account_name', datalake_analytics_name_type, options_list=('--account', '-n'), completer=None)
register_cli_argument('datalake analytics account update', 'firewall_state', help='Optionally enable/disable existing firewall rules.', **enum_choice_list(FirewallState))
register_cli_argument('datalake analytics account update', 'allow_azure_ips', help='Optionally allow/block Azure originating IPs through the firewall', **enum_choice_list(FirewallAllowAzureIpsState))
register_cli_argument('datalake analytics account update', 'max_job_count', help='The maximum supported jobs running under the account at the same time.', type=int)
register_cli_argument('datalake analytics account update', 'max_degree_of_parallelism', help='The maximum supported degree of parallelism for this account.', type=int)
register_cli_argument('datalake analytics account update', 'query_store_retention', help='The number of days that job metadata is retained.', type=int)
register_cli_argument('datalake analytics account list', 'resource_group_name', resource_group_name_type, validator=None)
# Job params
# pylint: disable=line-too-long
register_cli_argument('datalake analytics job submit', 'compile_mode', help='Optionally indicates the type of compilation to be done on this job. Valid values are: \'Semantic\' (Only performs semantic checks and necessary sanity checks), \'Full\' (full compilation) and \'SingleBox\' (Full compilation performed locally)', **enum_choice_list(CompileMode))
register_cli_argument('datalake analytics job submit', 'compile_only', help='Indicates that the submission should only build the job and not execute if set to true.', action='store_true')
register_cli_argument('datalake analytics job submit', 'script', completer=FilesCompleter(), help='The script to submit. This is either the script contents or use \'@<file path\' to load the script from a file')
register_cli_argument('datalake analytics job wait', 'max_wait_time_sec', help='The maximum amount of time to wait before erroring out. Default value is to never timeout. Any value <= 0 means never timeout', type=int)
register_cli_argument('datalake analytics job wait', 'wait_interval_sec', help='The polling interval between checks for the job status, in seconds.', type=int)
# credential params
register_cli_argument('datalake analytics catalog credential create', 'credential_user_password', options_list=('--password', '-p'), help='Password for the credential user. Will prompt if not given.')
register_cli_argument('datalake analytics catalog credential create', 'credential_user_name', options_list=('--user-name',))
register_cli_argument('datalake analytics catalog credential update', 'credential_user_name', options_list=('--user-name',))
register_cli_argument('datalake analytics catalog credential update', 'credential_user_password', options_list=('--password', '-p'), help='Current password for the credential user. Will prompt if not given.')
register_cli_argument('datalake analytics catalog credential update', 'new_credential_user_password', options_list=('--new-password',), help='New password for the credential user. Will prompt if not given.')
