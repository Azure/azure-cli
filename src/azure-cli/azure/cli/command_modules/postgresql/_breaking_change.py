# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import (register_argument_deprecate, register_command_group_deprecate,
                                            register_other_breaking_change)

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

# Server create command will stop creating new or altering existing network resources required for the
# server to function, such as virtual networks, subnets, IP ranges, etc. It will instead require users
# to provide the necessary network resources created beforehand using the corresponding commands from the
# `az network` module. That change will take effect in next breaking change release(2.86.0) scheduled for May 2026.
register_other_breaking_change('postgres flexible-server create',
                               message='This command will stop creating new network resources or altering '
                               'existing ones which are required for the server to function, such as virtual networks, '
                               'subnets, IP ranges, etc. It will instead require users to provide the necessary '
                               'network resources created beforehand using the corresponding commands from the '
                               '`az network` module. This change will take effect in next breaking change '
                               'release(2.86.0) scheduled for May 2026.')

# Replica create command will stop creating new or altering existing network resources required for the
# server to function, such as virtual networks, subnets, IP ranges, etc. It will instead require users
# to provide the necessary network resources created beforehand using the corresponding commands from the
# `az network` module. That change will take effect in next breaking change release(2.86.0) scheduled for May 2026.
register_other_breaking_change('postgres flexible-server replica create',
                               message='This command will stop creating new network resources or altering '
                               'existing ones which are required for the server to function, such as virtual networks, '
                               'subnets, IP ranges, etc. It will instead require users to provide the necessary '
                               'network resources created beforehand using the corresponding commands from the '
                               '`az network` module. This change will take effect in next breaking change '
                               'release(2.86.0) scheduled for May 2026.')

# Server restore command will stop creating new or altering existing network resources required for the server to
# function, such as virtual networks, subnets, IP ranges, etc. It will instead require users to provide the
# necessary network resources created beforehand using the corresponding commands from the `az network` module.
# That change will take effect in next breaking change release(2.86.0) scheduled for May 2026.
register_other_breaking_change('postgres flexible-server restore',
                               message='This command will stop creating new network resources or altering '
                               'existing ones which are required for the server to function, such as virtual networks, '
                               'subnets, IP ranges, etc. It will instead require users to provide the necessary '
                               'network resources created beforehand using the corresponding commands from the '
                               '`az network` module. This change will take effect in next breaking change '
                               'release(2.86.0) scheduled for May 2026.')

# Server geo-restore command will stop creating new or altering existing network resources required for the
# server to function, such as virtual networks, subnets, IP ranges, etc. It will instead require users to
# provide the necessary network resources created beforehand using the corresponding commands from the `az network` module.
# That change will take effect in next breaking change release(2.86.0) scheduled for May 2026.
register_other_breaking_change('postgres flexible-server geo-restore',
                               message='This command will stop creating new network resources or altering '
                               'existing ones which are required for the server to function, such as virtual networks, '
                               'subnets, IP ranges, etc. It will instead require users to provide the necessary '
                               'network resources created beforehand using the corresponding commands from the '
                               '`az network` module. This change will take effect in next breaking change '
                               'release(2.86.0) scheduled for May 2026.')


# Revive dropped server command will stop creating new or altering existing network resources required for the
# server to function, such as virtual networks, subnets, IP ranges, etc. It will instead require users to
# provide the necessary network resources created beforehand using the corresponding commands from the `az network` module.
# That change will take effect in next breaking change release(2.86.0) scheduled for May 2026.
register_other_breaking_change('postgres flexible-server revive-dropped',
                               message='This command will stop creating new network resources or altering '
                               'existing ones which are required for the server to function, such as virtual networks, '
                               'subnets, IP ranges, etc. It will instead require users to provide the necessary '
                               'network resources created beforehand using the corresponding commands from the '
                               '`az network` module. This change will take effect in next breaking change '
                               'release(2.86.0) scheduled for May 2026.')
