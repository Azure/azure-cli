# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import (
    register_argument_deprecate,
    register_command_group_deprecate,
    register_other_breaking_change
)

NETWORK_RESOURCE_BREAKING_CHANGE_MESSAGE = (
    'This command will stop creating new network resources or altering existing ones which are required '
    'for the server to function, such as virtual networks, subnets, IP ranges, etc. It will instead '
    'require users to provide the necessary network resources created beforehand using the corresponding '
    'commands from the `az network` module.'
)


def _register_network_resource_breaking_change(command_name):
    register_other_breaking_change(command_name, message=NETWORK_RESOURCE_BREAKING_CHANGE_MESSAGE)
    register_argument_deprecate(command_name, '--address-prefixes')
    register_argument_deprecate(command_name, '--subnet-prefixes')


# These commands will stop creating or altering required network resources and will instead require
# users to provide those resources up front using the corresponding `az network` commands.
# Parameters --address-prefixes and --subnet-prefixes will also be deprecated for these commands as part of this change.
for network_command in (
        'postgres flexible-server create',
        'postgres flexible-server replica create',
        'postgres flexible-server restore',
        'postgres flexible-server geo-restore',
        'postgres flexible-server revive-dropped'):
    _register_network_resource_breaking_change(network_command)


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
