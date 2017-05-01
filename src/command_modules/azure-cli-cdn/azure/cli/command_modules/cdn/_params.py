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

# pylint: disable=line-too-long
from azure.mgmt.datalake.analytics.account.models.data_lake_analytics_account_management_client_enums \
    import (FirewallState,
            TierType,
            FirewallAllowAzureIpsState)

from azure.mgmt.datalake.analytics.job.models.data_lake_analytics_job_management_client_enums \
    import (CompileMode,
            JobState,
            JobResult)
