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
sql_db_special_create_mode_params = ['create_mode', 'source_database_id', 'restorePointInTime']

with ParametersContext(command='sql db') as c:
    c.register_alias('database_name', ('--name', '-n'))
    c.register_alias('server_name', ('--server-name', '-s'))
    c.register_alias('requested_service_objective_name', ('--service-objective-name',))
    c.register_alias('requested_service_objective_id', ('--service-objective-id',))

def configure_db_create_params(c):
    from azure.mgmt.sql.models.database import Database
    c.expand('parameters', Database)

    # We have a wrapper function that determines server location so user doesn't need to specify it as param.
    # Also we have specific commands to special create modes which have their own required params, so
    # database properties related to create mode can be ignores
    ignores = ['location'] + sql_db_special_create_mode_params
    for p in ignores:
        c.ignore(p)

with ParametersContext(command='sql db create') as c:
    configure_db_create_params(c)

# The following params are ignored when creating a copy or secondary because their
# values are determined by the source db
sql_db_copy_ignored_params = ['collation', 'edition', 'max_size_bytes']

with ParametersContext(command='sql db copy') as c:
    configure_db_create_params(c)
    c.register_alias('requested_service_objective_name', ('--dest-service-objective-name',))
    c.register_alias('requested_service_objective_id', ('--dest-service-objective-id',))
    c.register_alias('elastic_pool_name', ('--dest-elastic-pool-name',))
    for i in sql_db_copy_ignored_params:
        c.ignore(i)

with ParametersContext(command='sql db create-secondary') as c:
    configure_db_create_params(c)
    c.register_alias('requested_service_objective_name', ('--secondary-service-objective-name',))
    c.register_alias('requested_service_objective_id', ('--secondary-service-objective-id',))
    c.register_alias('elastic_pool_name', ('--secondary-elastic-pool-name',))
    for i in sql_db_copy_ignored_params:
        c.ignore(i)

# The following params are ignored when restoring because their values are determined by the source db
sql_db_restore_ignored_params = ['collation', 'max_size_bytes']

with ParametersContext(command='sql db restore') as c:
    configure_db_create_params(c)
    c.register_alias('requested_service_objective_name', ('--dest-service-objective-name',))
    c.register_alias('requested_service_objective_id', ('--dest-service-objective-id',))
    c.register_alias('elastic_pool_name', ('--dest-elastic-pool-name',))
    for i in sql_db_restore_ignored_params:
        c.ignore(i)

with ParametersContext(command='sql db update') as c:
    from azure.mgmt.sql.models.database import Database
    c.expand('parameters', Database)

    # These parameters are applicable to create only, not update.
    ignores = ['location', 'collation'] + sql_db_special_create_mode_params
    for i in ignores:
        c.ignore(i)

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
    c.expand('parameters', ElasticPool)
    # We have a wrapper function that determines server location so user doesn't need to specify it as param.
    c.ignore('location')

with ParametersContext(command='sql elastic-pool update') as c:
    from azure.mgmt.sql.models.elastic_pool import ElasticPool
    c.expand('parameters', ElasticPool)
    # We have a wrapper function that determines server location so user doesn't need to specify it as param.
    c.ignore('location')

###############################################
#                sql server                   #
###############################################

with ParametersContext(command='sql server') as c:
    c.register_alias('server_name', ('--name', '-n'))
    c.register_alias('administrator_login', ('--admin-login', '-u'))
    c.register_alias('administrator_login_password', ('--admin-password', '-p'))

with ParametersContext(command='sql server create') as c:
    from azure.mgmt.sql.models.server import Server
    # - Both administrator_login and administrator_login_password are required for server creation.
    # However these two parameters are given default value in the create_or_update function
    # signature, therefore, they can't be automatically converted to requirement arguments.
    patches = {
        'administrator_login': patch_arg_make_required,
        'administrator_login_password': patch_arg_make_required
    }
    c.expand('parameters', Server, group_name='Authentication', patches=patches)

    # 12.0 is the only server version allowed and it's already the default.
    c.ignore('version')

with ParametersContext(command='sql server update') as c:
    from azure.mgmt.sql.models.server import Server
    c.expand('parameters', Server)

    # location and administrator_login cannot be updated.
    # 12.0 is the only server version allowed and it's already the default.
    for i in ['location', 'administrator_login', 'version']:
        c.ignore(i)

#####
#           sql server firewall-rule
#####

with ParametersContext(command='sql server firewall-rule') as c:
    c.register_alias('server_name', ('--server-name', '-s'))
    c.register_alias('firewall_rule_name', ('--name', '-n'))

#####
#           sql server service-objective
#####

with ParametersContext(command='sql server service-objective') as c:
    c.register_alias('server_name', ('--server-name', '-s'))
    c.register_alias('service_objective_name', ('--name', '-n'))

