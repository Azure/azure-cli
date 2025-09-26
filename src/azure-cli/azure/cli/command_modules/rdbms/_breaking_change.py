# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_logic_breaking_change, \
    register_argument_deprecate, register_other_breaking_change

register_logic_breaking_change('postgres flexible-server create', 'Update default value of "--version"',
                               detail='The default value will be changed from "17" to a '
                               'supported version based on regional capabilities.')
register_argument_deprecate('postgres flexible-server create', '--create-default-database',
                               message='Please use command group "postgres flexible-server db" for database creation.')
register_argument_deprecate('postgres flexible-server create', '--database-name',
                               message='Please use command group "postgres flexible-server db" for database creation.')
register_other_breaking_change('postgres server',
                               message='Azure Database for PostgreSQL Single Server is deprecated. '
                               'Please migrate to Flexible Server for new deployments.')
register_other_breaking_change('postgres db',
                               message='Azure Database for PostgreSQL Single Server is deprecated. '
                               'Please migrate to Flexible Server for new deployments.')
register_other_breaking_change('postgres server-logs',
                               message='Azure Database for PostgreSQL Single Server is deprecated. '
                               'Please migrate to Flexible Server for new deployments.')
register_argument_deprecate(
    'postgres flexible-server backup',
    '--backup-name',
    message='The argument "--backup-name" will be changed to "--name".'
)
register_argument_deprecate(
    'postgres flexible-server backup',
    '--name',
    message='The argument "--name" will be changed to "--server-name".'
)
register_argument_deprecate(
    'postgres flexible-server db',
    '--database-name',
    message='The argument "--database-name" will be changed to "--name".'
)
register_argument_deprecate(
    'postgres flexible-server firewall-rule',
    '--name',
    message='The argument "--name" will be changed to "--server-name".'
)
register_argument_deprecate(
    'postgres flexible-server firewall-rule',
    '--rule-name',
    message='The argument "--rule-name" will be changed to "--name".'
)
register_argument_deprecate(
    'postgres flexible-server long-term-retention',
    '--name',
    message='The argument "--name" will be changed to "--server-name".'
)
register_argument_deprecate(
    'postgres flexible-server migration',
    '--migration-name',
    message='The argument "--migration-name" will be changed to "--name".'
)
register_argument_deprecate(
    'postgres flexible-server migration',
    '--name',
    message='The argument "--name" will be changed to "--server-name".'
)
register_argument_deprecate(
    'postgres flexible-server replica',
    '--replica-name',
    message='The argument "--replica-name" will be changed to "--name".'
)
