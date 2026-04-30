# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import (
    NextBreakingChangeWindow,
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

# Index Tuning command group renamed to Autonomous Tuning as the feature has expanded to
# include more types of recommendations beyond just index tuning
register_command_group_deprecate(command_group='postgres flexible-server index-tuning',
                                 redirect='postgres flexible-server autonomous-tuning',
                                 message='Index tuning feature has now expanded its capabilities to support '
                                 'other automatically generated recommendations which are covered by the '
                                 'new command.')

# Long term retention command group deprecated with no redirect as the functionality will be removed in the future
register_command_group_deprecate(command_group='postgres flexible-server long-term-retention',
                                 message='Long term retention command group will be removed. '
                                 'For more information, open a support incident.')

# Upgrade command argument changes
register_other_breaking_change('postgres flexible-server upgrade',
                               message='The allowed values will be changed from set list to '
                               'supported versions for upgrade based on capabilities.',
                               arg='--version')

# Name of new backup no longer required in backup create command
register_other_breaking_change('postgres flexible-server backup create',
                               message='The argument for backup name will no longer be required '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')

# LTR command argument changes
register_other_breaking_change('postgres flexible-server long-term-retention',
                               message='The --backup-name/-b argument has been deprecated and will be removed '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')
register_other_breaking_change('postgres flexible-server long-term-retention',
                               message='The --name/-n argument will be repurposed to specify the backup name. '
                               'The --server-name/-s argument will be introduced to specify the server name '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')

# Backup command argument changes
register_other_breaking_change('postgres flexible-server backup',
                               message='The --backup-name/-b argument has been deprecated and will be removed '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')
register_other_breaking_change('postgres flexible-server backup',
                               message='The --name/-n argument will be repurposed to specify the backup name. '
                               'The --server-name/-s argument will be introduced to specify the server name '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')

# Database command argument changes
register_other_breaking_change('postgres flexible-server db',
                               message='The --database-name/-d argument has been deprecated and will be removed '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')
register_other_breaking_change('postgres flexible-server db',
                               message='The --name/-n argument will be repurposed to specify the database name. '
                               'The --server-name/-s argument will be introduced to specify the server name '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')

# Firewall rule command argument changes
register_other_breaking_change('postgres flexible-server firewall-rule',
                               message='The --name/-n argument will be repurposed to specify the firewall rule '
                               'name. The --server-name/-s argument will be introduced to specify the server '
                               'name in next breaking change release(2.86.0) scheduled for May 2026.')
register_other_breaking_change('postgres flexible-server firewall-rule',
                               message='The --rule-name/-r argument has been deprecated and will be removed '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')

# Migration command argument changes
register_other_breaking_change('postgres flexible-server migration',
                               message='The --migration-name argument has been deprecated and will be removed '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')
register_other_breaking_change('postgres flexible-server migration',
                               message='The --name/-n argument will be repurposed to specify the migration name. '
                               'The --server-name/-s argument will be introduced to specify the server name '
                               'in next breaking change release(2.86.0) scheduled for May 2026.')

# Replica command argument changes
register_argument_deprecate('postgres flexible-server replica create', '--replica-name', redirect='--name')

# Elastic cluster command argument deprecated and will be removed in the future. Today,
# users must specify both --cluster-option ElasticCluster and --node-count to create an
# elastic cluster. In the future, providing --node-count alone will imply an elastic cluster.
register_argument_deprecate(command='postgres flexible-server create', argument='--cluster-option',
                            message='Currently, to create an elastic cluster you must specify '
                            '--cluster-option ElasticCluster together with --node-count. In the '
                            'future, providing --node-count alone will imply an elastic cluster.',
                            target_version=NextBreakingChangeWindow())
