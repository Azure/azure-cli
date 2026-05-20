# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import (
    register_argument_deprecate,
    register_command_group_deprecate,
    register_other_breaking_change
)

# High availability command argument changes
register_argument_deprecate('postgres flexible-server create', '--high-availability', redirect='--zonal-resiliency')
register_argument_deprecate('postgres flexible-server update', '--high-availability', redirect='--zonal-resiliency')

# Long term retention command group deprecated with no redirect as the functionality will be removed in the future
register_command_group_deprecate(command_group='postgres flexible-server long-term-retention',
                                 message='Long term retention command group will be removed. '
                                 'For more information, open a support incident.')

# Name of new backup no longer required in backup create command
register_other_breaking_change('postgres flexible-server backup create',
                               message='The argument for backup name will no longer be required '
                               'in the next breaking change release (2.86.0) scheduled for May 2026.')
