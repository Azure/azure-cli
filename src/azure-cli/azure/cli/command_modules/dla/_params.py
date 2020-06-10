# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import (
    tags_type, get_resource_name_completion_list, resource_group_name_type, get_enum_type)

from azure.cli.command_modules.dla._validators import validate_resource_group_name, datetime_format


# pylint: disable=line-too-long, too-many-statements
def load_arguments(self, _):
    from azure.mgmt.datalake.analytics.account.models import (FirewallState, TierType, FirewallAllowAzureIpsState,
                                                              AADObjectType)

    from azure.mgmt.datalake.analytics.job.models import (CompileMode, JobState, JobResult)

    datalake_analytics_name_type = CLIArgumentType(help='Name of the Data Lake Analytics account.', options_list=('--account_name',), completer=get_resource_name_completion_list('Microsoft.DataLakeAnalytics/accounts'), id_part='name')

    # PARAMETER REGISTRATIONS
    # common
    with self.argument_context('dla') as c:
        c.argument('resource_group_name', resource_group_name_type, id_part=None, required=False, help='If not specified, will attempt to discover the resource group for the specified Data Lake Analytics account.', validator=validate_resource_group_name)
        c.argument('top', help='Maximum number of items to return.', type=int)
        c.argument('skip', help='The number of items to skip over before returning elements.', type=int)
        c.argument('count', help='The Boolean value of true or false to request a count of the matching resources included with the resources in the response, e.g. Categories?$count=true.', type=bool)
        c.argument('account_name', datalake_analytics_name_type, options_list=['--account', '-n'])

    # account
    with self.argument_context('dla account') as c:
        c.argument('tags', tags_type)
        c.argument('tier', arg_type=get_enum_type(TierType), help='The desired commitment tier for this account to use.')

    with self.argument_context('dla account create') as c:
        c.argument('resource_group_name', resource_group_name_type, validator=None)
        c.argument('account_name', datalake_analytics_name_type, options_list=('--account', '-n'), completer=None)

    with self.argument_context('dla account update') as c:
        c.argument('firewall_state', help='Enable/disable existing firewall rules.', arg_type=get_enum_type(FirewallState))
        c.argument('allow_azure_ips', help='Allow/block Azure originating IPs through the firewall', arg_type=get_enum_type(FirewallAllowAzureIpsState))
        c.argument('max_job_count', help='The maximum supported jobs running under the account at the same time.', type=int)
        c.argument('max_degree_of_parallelism', help='The maximum supported degree of parallelism for this account.', type=int)
        c.argument('query_store_retention', help='The number of days that job metadata is retained.', type=int)

    with self.argument_context('dla account list') as c:
        c.argument('resource_group_name', resource_group_name_type, validator=None)

    # storage
    with self.argument_context('dla account blob-storage') as c:
        c.argument('access_key', help='the access key associated with this Azure Storage account that will be used to connect to it')
        c.argument('suffix', help='the optional suffix for the storage account')
        c.argument('storage_account_name', help='Name of an existing storage account to link to.')

    # job
    with self.argument_context('dla job submit') as c:
        c.argument('compile_mode', arg_type=get_enum_type(CompileMode), help='Indicates the type of compilation to be done on this job. Valid values are: \'Semantic\' (Only performs semantic checks and necessary sanity checks), \'Full\' (full compilation) and \'SingleBox\' (Full compilation performed locally)')
        c.argument('compile_only', help='Indicates that the submission should only build the job and not execute if set to true.', action='store_true')
        c.argument('script', completer=FilesCompleter(), help="The script to submit. This is either the script contents or use `@<file path>` to load the script from a file")
        c.argument('pipeline_id', help='Job relationship pipeline GUID.')
        c.argument('pipeline_name', help='Friendly name of the job relationship pipeline.')
        c.argument('pipeline_uri', help='Unique pipeline URI which links to the originating service for this pipeline.')
        c.argument('run_id', help='GUID of the iteration of this pipeline.')
        c.argument('recurrence_id', help='Recurrence GUID, unique per activity/script, regardless of iteration. Links different occurrences of the same job together.')
        c.argument('recurrence_name', help='Friendly recurrence nae for the correlation between jobs.')

    with self.argument_context('dla job wait') as c:
        c.argument('max_wait_time_sec', help='The maximum amount of time to wait before erroring out. Default value is to never timeout. Any value <= 0 means never timeout', type=int)
        c.argument('wait_interval_sec', help='The polling interval between checks for the job status, in seconds.', type=int)

    with self.argument_context('dla job list') as c:
        c.argument('submitted_after', help='A filter which returns jobs only submitted after the specified time, in ISO-8601 format.', type=datetime_format)
        c.argument('submitted_before', help='A filter which returns jobs only submitted before the specified time, in ISO-8601 format.', type=datetime_format)
        c.argument('state', arg_type=get_enum_type(JobState), help='A filter which returns jobs with only the specified state(s).', nargs='*')
        c.argument('result', arg_type=get_enum_type(JobResult), help='A filter which returns jobs with only the specified result(s).', nargs='*')
        c.argument('submitter', help='A filter which returns jobs only by the specified submitter.')
        c.argument('name', help='A filter which returns jobs only by the specified friendly name.')
        c.argument('pipeline_id', help='A filter which returns jobs only containing the specified pipeline_id.')
        c.argument('recurrence_id', help='A filter which returns jobs only containing the specified recurrence_id.')

    # credential
    with self.argument_context('dla catalog credential') as c:
        c.argument('uri', help='URI of the external data source.')

    with self.argument_context('dla catalog credential create') as c:
        c.argument('credential_user_password', options_list=['--password', '-p'], help='Password for the credential user. Will prompt if not given.')
        c.argument('credential_user_name', options_list=['--user-name'])

    with self.argument_context('dla catalog credential update') as c:
        c.argument('credential_user_name', options_list=['--user-name'])
        c.argument('credential_user_password', options_list=['--password', '-p'], help='Current password for the credential user. Will prompt if not given.')
        c.argument('new_credential_user_password', options_list=['--new-password'], help='New password for the credential user. Will prompt if not given.')

    # compute policy
    with self.argument_context('dla account compute_policy') as c:
        c.argument('max_dop_per_job', help='The maximum degree of parallelism allowed per job for this policy. At least one of --min-priority-per-job and --max-dop-per-job must be specified.', type=int)
        c.argument('min_priority_per_job', help='The minimum priority allowed per job for this policy. At least one of --min-priority-per-job and --max-dop-per-job must be specified.', type=int)

    with self.argument_context('dla account compute_policy create') as c:
        c.argument('object_id', help='The Azure Active Directory object ID of the user, group or service principal to apply the policy to.')
        c.argument('object_type', arg_type=get_enum_type(AADObjectType), help='The Azure Active Directory object type associated with the supplied object id.')
