# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import ParametersContext, patch_arg_make_required
from azure.cli.core.commands import CliArgumentType
from azure.mgmt.sql.models.elastic_pool import ElasticPool
from azure.mgmt.sql.models.server import Server

#####
#           Reusable param type definitions
#####

server_param_type = CliArgumentType(
    options_list=('--server', '-s'),
    help='Name of the Azure SQL server.')

###############################################
#                sql db                       #
###############################################

# sql db params that are used for non-default create modes. These are ignored
# for regular create (because we have custom commands for special create modes)
# and ignored for update (because they are not applicable to update)
sql_db_special_create_mode_params = ['create_mode', 'source_database_id', 'restorePointInTime']

with ParametersContext(command='sql db') as c:
    c.argument('database_name',
               options_list=('--name', '-n'),
               help='Name of the Azure SQL Database.')
    c.argument('server_name', arg_type=server_param_type)
    c.register_alias('elastic_pool_name', ('--elastic-pool',))
    c.register_alias('requested_service_objective_name', ('--service-objective',))
    c.register_alias('requested_service_objective_id', ('--service-objective-id',))


def configure_db_create_params(cmd):
    from azure.mgmt.sql.models.database import Database
    cmd.expand('parameters', Database)

    # Adjust help text.
    cmd.argument('edition',
                 options_list=('--edition',),
                 help='The edition of the Azure SQL database.')

    # We have a wrapper function that determines server location so user doesn't need to specify
    # it as param. Also we have specific commands to special create modes which have their own
    # required params, so database properties related to create mode can be ignored
    ignores = ['location'] + sql_db_special_create_mode_params
    for p in ignores:
        cmd.ignore(p)


with ParametersContext(command='sql db create') as c:
    configure_db_create_params(c)

# The following params are ignored when creating a copy or secondary because their
# values are determined by the source db
sql_db_copy_ignored_params = ['collation', 'edition', 'max_size_bytes']

with ParametersContext(command='sql db copy') as c:
    configure_db_create_params(c)

    c.argument('elastic_pool_name',
               options_list=('--dest-elastic-pool',),
               help='Name of elastic pool to create the new database in.')

    c.argument('dest_name',
               help='Name of the database that will be created as the copy destinaton.')

    c.argument('dest_resource_group_name',
               options_list=('--dest-resource-group',),
               help='Name of the resouce group to create the copy in.'
               ' If unspecified, defaults to the origin resource group.')

    c.argument('dest_server_name',
               options_list=('--dest-server',),
               help='Name of the server to create the copy in.'
               ' If unspecified, defaults to the origin server.')

    c.argument('requested_service_objective_name',
               options_list=('--dest-service-objective',),
               help='Name of service objective for the new database.')

    c.argument('requested_service_objective_id',
               options_list=('--dest-service-objective-id',),
               help='Id of service objective for the new database.')

    for i in sql_db_copy_ignored_params:
        c.ignore(i)

with ParametersContext(command='sql db create-replica') as c:
    configure_db_create_params(c)

    c.argument('elastic_pool_name',
               options_list=('--dest-elastic-pool',),
               help='Name of elastic pool to create the new database in.')

    c.argument('requested_service_objective_name',
               options_list=('--secondary-service-objective',),
               help='Name of service objective for the new secondary database.')

    c.argument('requested_service_objective_id',
               options_list=('--secondary-service-objective-id',),
               help='Id of service objective for the new secondary database.')

    c.argument('secondary_resource_group_name',
               options_list=('--secondary-resource-group',),
               help='Name of the resource group to create the new secondary database in.'
               ' If unspecified, defaults to the origin resource group.')

    c.argument('secondary_server_name',
               options_list=('--secondary-server',),
               help='Name of the server to create the new secondary database in.')

    for i in sql_db_copy_ignored_params:
        c.ignore(i)

# The following params are ignored when restoring because their values are determined by the
# source db
sql_db_restore_ignored_params = ['collation', 'max_size_bytes']

with ParametersContext(command='sql db restore') as c:
    configure_db_create_params(c)
    c.register_alias('requested_service_objective_name', ('--dest-service-objective',))
    c.register_alias('requested_service_objective_id', ('--dest-service-objective-id',))
    c.register_alias('elastic_pool_name', ('--dest-elastic-pool',))
    c.register_alias('dest_resource_group_name', ('--dest-resource-group',))
    for i in sql_db_restore_ignored_params:
        c.ignore(i)

with ParametersContext(command='sql db show') as c:
    # Service tier advisors and transparent data encryption are not included in the first batch
    # of GA commands.
    c.ignore('expand')

with ParametersContext(command='sql db list') as c:
    c.argument('elastic_pool_name',
               help='If specified, lists only the databases in this elastic pool')

with ParametersContext(command='sql db update') as c:
    c.argument('requested_service_objective_name',
               help='The name of the new service objective. If this is a standalone db service'
               ' objective and the db is currently in an elastic pool, then the db is removed from'
               ' the pool.')
    c.argument('elastic_pool_name', help='The name of the elastic pool to move the database into.')
    c.argument('max_size_bytes', help='The new maximum size of the database expressed in bytes.')

#####
#           sql db replica-link
#####

with ParametersContext(command='sql db replica-link') as c:
    c.register_alias('database_name', ('--database', '-d'))
    c.register_alias('link_id', ('--name', '-n'))

#####
#           sql db <<other subgroups>>
#####

# Data Warehouse will not be included in the first batch of GA commands
# with ParametersContext(command='sql db data-warehouse') as c:
#     c.register_alias('database_name', ('--database', '-d'))

# Data Warehouse will not be included in the first batch of GA commands
# (list_restore_points also applies to db, but it's not very useful. It's
# mainly useful for dw.)
# with ParametersContext(command='sql db restore-point') as c:
#     c.register_alias('database_name', ('--database', '-d'))

# Service tier advisor will not be included in the first batch of GA commands
# with ParametersContext(command='sql db service-tier-advisor') as c:
#     c.register_alias('database_name', ('--database', '-d'))

# TDE will not be included in the first batch of GA commands
# with ParametersContext(command='sql db transparent-data-encryption') as c:
#     c.register_alias('database_name', ('--database', '-d'))

###############################################
#                sql elastic-pool             #
###############################################

with ParametersContext(command='sql elastic-pool') as c:
    c.argument('elastic_pool_name',
               options_list=('--name', '-n'),
               help='The name of the elastic pool.')

# Recommended elastic pools will not be included in the first batch of GA commands
# with ParametersContext(command='sql elastic-pool recommended') as c:
#     c.register_alias('recommended_elastic_pool_name', ('--name', '-n'))

# with ParametersContext(command='sql elastic-pool recommended db') as c:
#     c.register_alias('recommended_elastic_pool_name', ('--recommended-elastic-pool',))
#     c.register_alias('database_name', ('--name', '-n'))

with ParametersContext(command='sql elastic-pool') as c:
    c.argument('server_name', arg_type=server_param_type)
    c.register_alias('database_dtu_max', ('--db-dtu-max',))
    c.register_alias('database_dtu_min', ('--db-dtu-min',))

with ParametersContext(command='sql elastic-pool create') as c:
    c.expand('parameters', ElasticPool)
    # We have a wrapper function that determines server location so user doesn't need to specify
    # it as param.
    c.ignore('location')

with ParametersContext(command='sql elastic-pool update') as c:
    c.argument('database_dtu_max', help='The maximum DTU any one database can consume.')
    c.argument('database_dtu_min', help='The minimum DTU all databases are guaranteed.')
    c.argument('dtu', help='TThe total shared DTU for the elastic eool.')
    c.argument('storage_mb', help='Storage limit for the elastic pool in MB.')

###############################################
#                sql server                   #
###############################################

with ParametersContext(command='sql server') as c:
    c.register_alias('server_name', ('--name', '-n'))
    c.register_alias('administrator_login', ('--admin-user', '-u'))
    c.register_alias('administrator_login_password', ('--admin-password', '-p'))

with ParametersContext(command='sql server create') as c:
    # Both administrator_login and administrator_login_password are required for server creation.
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
    c.argument('administrator_login_password', help='The administrator login password.')

#####
#           sql server firewall-rule
#####

with ParametersContext(command='sql server firewall-rule') as c:
    # Help text needs to be specified because 'sql server firewall-rule update' is a custom
    # command.
    c.argument('server_name',
               options_list=('--server', '-s'),
               help='The name of the Azure SQL server.')

    c.argument('firewall_rule_name',
               options_list=('--name', '-n'),
               help='The name of the firewall rule.')

    c.argument('start_ip_address',
               options_list=('--start-ip-address',),
               help='The start IP address of the firewall rule. Must be IPv4 format. Use value'
               ' \'0.0.0.0\' to represent all Azure-internal IP addresses.')

    c.argument('end_ip_address',
               options_list=('--end-ip-address',),
               help='The end IP address of the firewall rule. Must be IPv4 format. Use value'
               ' \'0.0.0.0\' to represent all Azure-internal IP addresses.')

#####
#           sql server service-objective
#####

with ParametersContext(command='sql server service-objective') as c:
    c.register_alias('server_name', ('--server', '-s'))
    c.register_alias('service_objective_name', ('--name', '-n'))
