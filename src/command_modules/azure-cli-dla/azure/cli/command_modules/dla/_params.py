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

from azure.cli.command_modules.dla._validators import (validate_resource_group_name,
                                                       datetime_format)


from azure.mgmt.datalake.analytics.account.models.data_lake_analytics_account_management_client_enums \
    import (FirewallState,
            TierType,
            FirewallAllowAzureIpsState)

from azure.mgmt.datalake.analytics.job.models.data_lake_analytics_job_management_client_enums \
    import (CompileMode,
            JobState,
            JobResult)


# ARGUMENT DEFINITIONS
# pylint: disable=line-too-long
datalake_analytics_name_type = CliArgumentType(help='Name of the Data Lake Analytics account.', options_list=('--account_name',), completer=get_resource_name_completion_list('Microsoft.DataLakeAnalytics/accounts'), id_part='name')

# PARAMETER REGISTRATIONS
# data lake analytics common params
register_cli_argument('dla', 'resource_group_name', resource_group_name_type, id_part=None, required=False, help='If not specified, will attempt to discover the resource group for the specified Data Lake Analytics account.', validator=validate_resource_group_name)
register_cli_argument('dla', 'top', help='Maximum number of items to return.', type=int)
register_cli_argument('dla', 'skip', help='The number of items to skip over before returning elements.', type=int)
register_cli_argument('dla', 'count', help='The Boolean value of true or false to request a count of the matching resources included with the resources in the response, e.g. Categories?$count=true.', type=bool)

# account params
register_cli_argument('dla', 'account_name', datalake_analytics_name_type, options_list=('--account', '-n'))
register_cli_argument('dla account', 'tags', tags_type)
register_cli_argument('dla account', 'tier', help='The desired commitment tier for this account to use.', **enum_choice_list(TierType))
register_cli_argument('dla account create', 'resource_group_name', resource_group_name_type, validator=None)
register_cli_argument('dla account create', 'account_name', datalake_analytics_name_type, options_list=('--account', '-n'), completer=None)
register_cli_argument('dla account update', 'firewall_state', help='Enable/disable existing firewall rules.', **enum_choice_list(FirewallState))
register_cli_argument('dla account update', 'allow_azure_ips', help='Allow/block Azure originating IPs through the firewall', **enum_choice_list(FirewallAllowAzureIpsState))
register_cli_argument('dla account update', 'max_job_count', help='The maximum supported jobs running under the account at the same time.', type=int)
register_cli_argument('dla account update', 'max_degree_of_parallelism', help='The maximum supported degree of parallelism for this account.', type=int)
register_cli_argument('dla account update', 'query_store_retention', help='The number of days that job metadata is retained.', type=int)
register_cli_argument('dla account list', 'resource_group_name', resource_group_name_type, validator=None)

# Job params
# pylint: disable=line-too-long
register_cli_argument('dla job submit', 'compile_mode', help='Indicates the type of compilation to be done on this job. Valid values are: \'Semantic\' (Only performs semantic checks and necessary sanity checks), \'Full\' (full compilation) and \'SingleBox\' (Full compilation performed locally)', **enum_choice_list(CompileMode))
register_cli_argument('dla job submit', 'compile_only', help='Indicates that the submission should only build the job and not execute if set to true.', action='store_true')
register_cli_argument('dla job submit', 'script', completer=FilesCompleter(), help="The script to submit. This is either the script contents or use `@<file path>` to load the script from a file")
register_cli_argument('dla job wait', 'max_wait_time_sec', help='The maximum amount of time to wait before erroring out. Default value is to never timeout. Any value <= 0 means never timeout', type=int)
register_cli_argument('dla job wait', 'wait_interval_sec', help='The polling interval between checks for the job status, in seconds.', type=int)
register_cli_argument('dla job list', 'submitted_after', help='A filter which returns jobs only submitted after the specified time, in ISO-8601 format.', type=datetime_format)
register_cli_argument('dla job list', 'submitted_before', help='A filter which returns jobs only submitted before the specified time, in ISO-8601 format.', type=datetime_format)
register_cli_argument('dla job list', 'state', help='A filter which returns jobs with only the specified state(s).', nargs='*', **enum_choice_list(JobState))
register_cli_argument('dla job list', 'result', help='A filter which returns jobs with only the specified result(s).', nargs='*', **enum_choice_list(JobResult))
register_cli_argument('dla job list', 'submitter', help='A filter which returns jobs only by the specified submitter.')
register_cli_argument('dla job list', 'name', help='A filter which returns jobs only by the specified friendly name.')

# credential params
register_cli_argument('dla catalog credential create', 'credential_user_password', options_list=('--password', '-p'), help='Password for the credential user. Will prompt if not given.')
register_cli_argument('dla catalog credential create', 'credential_user_name', options_list=('--user-name',))
register_cli_argument('dla catalog credential update', 'credential_user_name', options_list=('--user-name',))
register_cli_argument('dla catalog credential update', 'credential_user_password', options_list=('--password', '-p'), help='Current password for the credential user. Will prompt if not given.')
register_cli_argument('dla catalog credential update', 'new_credential_user_password', options_list=('--new-password',), help='New password for the credential user. Will prompt if not given.')
