# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import (
    register_argument_deprecate,
    register_other_breaking_change
)

# High availability command argument changes
register_argument_deprecate('postgres flexible-server create', '--high-availability', redirect='--zonal-resiliency')
register_argument_deprecate('postgres flexible-server update', '--high-availability', redirect='--zonal-resiliency')

# Name of new backup no longer required in backup create command
register_other_breaking_change('postgres flexible-server backup create',
                               message='The argument for backup name will no longer be required '
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
