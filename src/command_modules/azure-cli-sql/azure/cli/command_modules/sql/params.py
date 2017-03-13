# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import itertools
from enum import Enum
from ._util import ParametersContext, patch_arg_make_required
from azure.cli.core.commands import CliArgumentType
from azure.mgmt.sql.models.database import Database
from azure.mgmt.sql.models.elastic_pool import ElasticPool
from azure.mgmt.sql.models.server import Server
from azure.mgmt.sql.models.sql_management_client_enums import CreateMode

#####
#           Reusable param type definitions
#####


server_param_type = CliArgumentType(
    options_list=('--server', '-s'),
    help='Name of the Azure SQL server.')


#####
#           SizeWithUnitConverter - consider moving to common code (azure.cli.commands.parameters)
#####


class SizeWithUnitConverter(object):  # pylint: disable=too-few-public-methods

    def __init__(
            self,
            unit='kB',
            result_type=int,
            unit_map=None):
        self.unit = unit
        self.result_type = result_type
        self.unit_map = unit_map or dict(B=1, kB=1024, MB=1024 * 1024, GB=1024 * 1024 * 1024,
                                         TB=1024 * 1024 * 1024 * 1024)

    def __call__(self, value):
        numeric_part = ''.join(itertools.takewhile(str.isdigit, value))
        unit_part = value[len(numeric_part):]

        try:
            uvals = (self.unit_map[unit_part] if unit_part else 1) / \
                (self.unit_map[self.unit] if self.unit else 1)
            return self.result_type(uvals) * self.result_type(numeric_part)
        except KeyError:
            raise ValueError()

    def __repr__(self):
        return 'Size (in {}) - valid units are {}.'.format(
            self.unit,
            ', '.join(sorted(self.unit_map, key=self.unit_map.__getitem__)))


###############################################
#                sql db                       #
###############################################


class Engine(Enum):  # pylint: disable=too-few-public-methods
    """SQL RDBMS engine type."""
    db = 'db'
    dw = 'dw'


def _configure_db_create_params(
        cmd,
        engine,
        create_mode):
    """
    Configures params for db/dw create/update commands.

    The PUT database REST API has many parameters and many modes (`create_mode`) that control
    which parameters are valid. To make it easier for CLI users to get the param combinations
    correct, these create modes are separated into different commands (e.g.: create, copy,
    restore, etc).

    On top of that, some create modes and some params are not allowed if the database edition is
    DataWarehouse. For this reason, regular database commands are separated from datawarehouse
    commands (`db` vs `dw`.)

    As a result, the param combination matrix is a little complicated. This function configures
    which params are ignored for a PUT database command based on a command's SQL engine type and
    create mode.

    engine: Engine enum value (e.g. `db`, `dw`)
    create_mode: Valid CreateMode enum value (e.g. `default`, `copy`, etc)
    """

    # DW does not support all create modes. Check that engine and create_mode are consistent.
    if engine == Engine.dw and create_mode not in [
            CreateMode.default,
            CreateMode.point_in_time_restore,
            CreateMode.restore]:
        raise ValueError('Engine {} does not support create mode {}'.format(engine, create_mode))

    # Make restore point in time required for restore mode only
    if create_mode in [CreateMode.restore, CreateMode.point_in_time_restore]:
        patches = {
            'restore_point_in_time': patch_arg_make_required
        }
    else:
        patches = {}

    # Include all Database params as a starting point. We will filter from there.
    cmd.expand('parameters', Database, patches=patches)

    # The following params are always ignored because their values are filled in by wrapper
    # functions.
    cmd.ignore('location')
    cmd.ignore('create_mode')
    cmd.ignore('source_database_id')

    # Read scale is only applicable to sql db (not dw). However it is a preview feature and will
    # be not exposed for now.
    cmd.ignore('read_scale')

    # Service objective id is not user-friendly and won't be exposed.
    # Better to use service objective name instead.
    cmd.ignore('requested_service_objective_id')

    # Only applicable to default create mode. Also only applicable to db.
    if create_mode != CreateMode.default or engine != Engine.db:
        cmd.ignore('sample_name')

    # Only applicable to point in time restore create mode.
    if create_mode not in [CreateMode.restore, CreateMode.point_in_time_restore]:
        cmd.ignore('restore_point_in_time')

    # 'collation', 'edition', and 'max_size_bytes' are ignored (or rejected) when creating a copy
    # or secondary because their values are determined by the source db.
    if create_mode in [CreateMode.copy, CreateMode.non_readable_secondary,
                       CreateMode.online_secondary]:
        cmd.ignore('collation')
        cmd.ignore('edition')
        cmd.ignore('max_size_bytes')

    # collation and max_size_bytes are ignored when restoring because their values are determined by
    # the source db.
    if create_mode in [CreateMode.restore, CreateMode.point_in_time_restore]:
        cmd.ignore('collation')
        cmd.ignore('max_size_bytes')

    if engine == Engine.dw:
        # Elastic pool is only for SQL DB.
        c.ignore('elastic_pool_name')

        # Edition is always 'DataWarehouse'
        c.ignore('edition')


with ParametersContext(command='sql db') as c:
    c.argument('database_name',
               options_list=('--name', '-n'),
               help='Name of the Azure SQL Database.')
    c.argument('server_name', arg_type=server_param_type)
    c.register_alias('elastic_pool_name', ('--elastic-pool',))
    c.register_alias('requested_service_objective_name', ('--service-objective',))

    c.argument('max_size_bytes', options_list=('--max-size',),
               type=SizeWithUnitConverter('B', result_type=int),
               help='The max storage size of the database. Only the following'
               ' sizes are supported (in addition to limitations being placed on'
               ' each edition): 100MB, 500MB, 1GB, 5GB, 10GB, 20GB,'
               ' 30GB, 150GB, 200GB, 500GB. If no unit is specified, defaults to bytes (B).')

    # Adjust help text.
    c.argument('edition',
               options_list=('--edition',),
               help='The edition of the database.')


with ParametersContext(command='sql db create') as c:
    _configure_db_create_params(c, Engine.db, CreateMode.default)


with ParametersContext(command='sql db copy') as c:
    _configure_db_create_params(c, Engine.db, CreateMode.copy)

    c.argument('elastic_pool_name',
               help='Name of the elastic pool to create the new database in.')

    c.argument('dest_name',
               help='Name of the database that will be created as the copy destination.')

    c.argument('dest_resource_group_name',
               options_list=('--dest-resource-group',),
               help='Name of the resouce group to create the copy in.'
               ' If unspecified, defaults to the origin resource group.')

    c.argument('dest_server_name',
               options_list=('--dest-server',),
               help='Name of the server to create the copy in.'
               ' If unspecified, defaults to the origin server.')

    c.argument('requested_service_objective_name',
               options_list=('--service-objective',),
               help='Name of the service objective for the new database.')


with ParametersContext(command='sql db create-replica') as c:
    _configure_db_create_params(c, Engine.db, CreateMode.online_secondary)

    c.argument('elastic_pool_name',
               help='Name of the elastic pool to create the new database in.')

    c.argument('requested_service_objective_name',
               options_list=('--service-objective',),
               help='Name of the service objective for the new secondary database.')

    c.argument('secondary_resource_group_name',
               options_list=('--secondary-resource-group',),
               help='Name of the resource group to create the new secondary database in.'
               ' If unspecified, defaults to the origin resource group.')

    c.argument('secondary_server_name',
               options_list=('--secondary-server',),
               help='Name of the server to create the new secondary database in.')


with ParametersContext(command='sql db restore') as c:
    _configure_db_create_params(c, Engine.db, CreateMode.point_in_time_restore)

    c.argument('dest_name',
               help='Name of the database that will be created as the restore destination.')

    c.argument('restore_point_in_time',
               options_list=('--time', '-t'),
               help='The point in time of the source database that will be restored to create the'
               ' new database. Must be greater than or equal to the source database\'s'
               ' earliestRestoreDate value.')

    c.argument('edition',
               help='The edition for the new database.')
    c.argument('elastic_pool_name',
               help='Name of the elastic pool to create the new database in.')
    c.argument('requested_service_objective_name',
               help='Name of service objective for the new database.')


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
#           sql db replica
#####


with ParametersContext(command='sql db replica create') as c:
    _configure_db_create_params(c, Engine.db, CreateMode.online_secondary)

    c.argument('elastic_pool_name',
               options_list=('--elastic-pool',),
               help='Name of elastic pool to create the new replica in.')

    c.argument('requested_service_objective_name',
               options_list=('--service-objective',),
               help='Name of service objective for the new replica.')

    c.argument('partner_resource_group_name',
               options_list=('--partner-resource-group',),
               help='Name of the resource group to create the new replica in.'
               ' If unspecified, defaults to the origin resource group.')

    c.argument('partner_server_name',
               options_list=('--partner-server',),
               help='Name of the server to create the new replica in.')


with ParametersContext(command='sql db replica set-primary') as c:
    c.argument('database_name', help='Name of the database to fail over.')
    c.argument('server_name',
               help='Name of the server containing the secondary replica that will become'
               ' the new primary.')
    c.argument('resource_group_name',
               help='Name of the resource group containing the secondary replica that'
               ' will become the new primary.')
    c.argument('allow_data_loss',
               help='If specified, the failover operation will allow data loss.')

with ParametersContext(command='sql db replica delete-link') as c:
    c.argument('partner_server_name',
               options_list=('--partner-server',),
               help='Name of the server that the other replica is in.')
    c.argument('partner_resource_group_name',
               options_list=('--partner-resource-group',),
               help='Name of the resource group that the other replica is in. If unspecified,'
               ' defaults to the first database\'s resource group.')


#####
#           sql db <<other subgroups>>
#####


# Service tier advisor will not be included in the first batch of GA commands
# with ParametersContext(command='sql db service-tier-advisor') as c:
#     c.register_alias('database_name', ('--database', '-d'))

# TDE will not be included in the first batch of GA commands
# with ParametersContext(command='sql db transparent-data-encryption') as c:
#     c.register_alias('database_name', ('--database', '-d'))


###############################################
#                sql dw                       #
###############################################

with ParametersContext(command='sql dw') as c:
    c.argument('database_name', options_list=('--name', '-n'),
               help='Name of the data warehouse.')

    c.argument('server_name', arg_type=server_param_type)

    c.argument('max_size_bytes', options_list=('--max-size',),
               type=SizeWithUnitConverter('B', result_type=int),
               help='The max storage size of the data warehouse. If no unit is specified, defaults'
               'to bytes (B).')

    c.argument('requested_service_objective_name',
               options_list=('--service-objective',),
               help='The service objective of the data warehouse.')

    c.argument('collation',
               options_list=('--collation',),
               help='The collation of the data warehouse.')


with ParametersContext(command='sql dw create') as c:
    _configure_db_create_params(c, Engine.dw, CreateMode.default)


with ParametersContext(command='sql dw show') as c:
    # Service tier advisors and transparent data encryption are not included in the first batch
    # of GA commands.
    c.ignore('expand')


# Data Warehouse restore will not be included in the first batch of GA commands
# (list_restore_points also applies to db, but it's not very useful. It's
# mainly useful for dw.)
# with ParametersContext(command='sql dw restore-point') as c:
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

    c.argument('storage_mb', options_list=('--storage',),
               type=SizeWithUnitConverter('MB', result_type=int),
               help='The max storage size of the elastic pool. If no unit is specified, defaults'
               ' to megabytes (MB).')


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
    c.expand('parameters', Server, group_name='Authentication', patches={
        'administrator_login': patch_arg_make_required,
        'administrator_login_password': patch_arg_make_required
    })

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
