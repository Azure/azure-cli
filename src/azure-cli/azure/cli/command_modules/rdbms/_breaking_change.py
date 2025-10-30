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
