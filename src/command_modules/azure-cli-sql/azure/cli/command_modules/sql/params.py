# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import ParametersContext, patch_arg_make_required
from azure.cli.core.commands import register_cli_argument, register_extra_cli_argument

###############################################
#                sql db                       #
###############################################

# sql db params that are used for non-default create modes. These are ignored
# for regular create (because we have custom commands for special create modes)
# and ignored for update (because they are not applicable to update)
sql_db_special_create_mode_params = ['create_mode', 'source_database_id']

with ParametersContext(command='sql db') as c:
    c.register_alias('database_name', ('--name', '-n'))
    c.register_alias('server_name', ('--server-name', '-s'))
    c.register_alias('requested_service_objective_name', ('--service-objective-name',))
    c.register_alias('requested_service_objective_id', ('--service-objective-id',))

with ParametersContext(command='sql db create') as c:
    # We have a wrapper function that determines server location so user doesn't need to specify it as param.
    # Also we have specific commands to special create modes, so they can be ignored
    # for regular db create.
    ignores = ['location'] + sql_db_special_create_mode_params

    from azure.mgmt.sql.models.database import Database
    c.expand('parameters', Database, ignores=ignores)

with ParametersContext(command='sql db create-copy') as c:
    # Wrapper function determines location and create mode params
    ignores = ['location'] + sql_db_special_create_mode_params

    from azure.mgmt.sql.models.database import Database
    c.expand('parameters', Database, ignores=ignores)

with ParametersContext(command='sql db create-replica') as c:
    # Wrapper function determines location and create mode params
    ignores = ['location'] + sql_db_special_create_mode_params

    from azure.mgmt.sql.models.database import Database
    c.expand('parameters', Database, ignores=ignores)

with ParametersContext(command='sql db update') as c:
    # These parameters are applicable to create only, not update.
    ignores = ['location', 'collation'] + sql_db_special_create_mode_params

    from azure.mgmt.sql.models.database import Database
    c.expand('parameters', Database, ignores=ignores)

#####
#           sql db replication-link
#####

with ParametersContext(command='sql db replication-link') as c:
    c.register_alias('database_name', ('--database-name', '-d'))

#####
#           sql db <<other subgroups>>
#####

## Data Warehouse will not be included in the first batch of GA commands
#with ParametersContext(command='sql db data-warehouse') as c:
#    c.register_alias('database_name', ('--database-name',))

## Data Warehouse will not be included in the first batch of GA commands
## (list_restore_points also applies to db, but it's not very useful. It's
## mainly useful for dw.)
#with ParametersContext(command='sql db restore-point') as c:
#    c.register_alias('database_name', ('--database-name', '-d'))

## Service tier advisor will not be included in the first batch of GA commands
#with ParametersContext(command='sql db service-tier-advisor') as c:
#    c.register_alias('database_name', ('--database-name',))

## TDE will not be included in the first batch of GA commands
#with ParametersContext(command='sql db transparent-data-encryption') as c:
#    c.register_alias('database_name', ('--database-name',))

###############################################
#                sql elastic-pool             #
###############################################

with ParametersContext(command='sql elastic-pool') as c:
    c.register_alias('elastic_pool_name', ('--name', '-n'))

## Recommended elastic pools will not be included in the first batch of GA commands
#with ParametersContext(command='sql elastic-pool recommended') as c:
#    c.register_alias('recommended_elastic_pool_name', ('--name', '-n'))

#with ParametersContext(command='sql elastic-pool recommended db') as c:
#    c.register_alias('recommended_elastic_pool_name', ('--recommended-elastic-pool-name',))
#    c.register_alias('database_name', ('--name', '-n'))

with ParametersContext(command='sql elastic-pool') as c:
    c.register_alias('server_name', ('--server-name', '-s'))

with ParametersContext(command='sql elastic-pool create') as c:
    from azure.mgmt.sql.models.elastic_pool import ElasticPool
    # We have a wrapper function that determines server location so user doesn't need to specify it as param.
    c.expand('parameters', ElasticPool, ignores=['location'])

with ParametersContext(command='sql elastic-pool update') as c:
    from azure.mgmt.sql.models.elastic_pool import ElasticPool
    # We have a wrapper function that determines server location so user doesn't need to specify it as param.
    c.expand('parameters', ElasticPool, ignores=['location'])

###############################################
#                sql server                   #
###############################################

with ParametersContext(command='sql server') as c:
    c.register_alias('server_name', ('--name', '-n'))
    c.register_alias('administrator_login', ('--admin-login', '-u'))
    c.register_alias('administrator_login_password', ('--admin-password', '-p'))

with ParametersContext(command='sql server create') as c:
    from azure.mgmt.sql.models.server import Server

    # 12.0 is the only server version allowed and it's already the default.
    ignores = ['version']

    # - Both administrator_login and administrator_login_password are required for server creation.
    # However these two parameters are given default value in the create_or_update function
    # signature, therefore, they can't be automatically converted to requirement arguments.
    patches = {
        'administrator_login': patch_arg_make_required,
        'administrator_login_password': patch_arg_make_required
    }

    c.expand('parameters', Server, group_name='Authentication', ignores=ignores, patches=patches)

with ParametersContext(command='sql server update') as c:
    from azure.mgmt.sql.models.server import Server

    # location and administrator_login cannot be updated.
    # 12.0 is the only server version allowed and it's already the default.
    ignores = ['location', 'administrator_login', 'version']
    c.expand('parameters', Server, ignores=ignores)

#####
#           sql server firewall
#####

with ParametersContext(command='sql server firewall') as c:
    c.register_alias('server_name', ('--server-name', '-s'))
    c.register_alias('firewall_rule_name', ('--name', '-n'))

#####
#           sql server service-objective
#####

with ParametersContext(command='sql server service-objective') as c:
    c.register_alias('server_name', ('--server-name', '-s'))
    c.register_alias('service_objective_name', ('--name', '-n'))

