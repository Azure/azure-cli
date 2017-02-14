# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import ParametersContext, patch_arg_make_required


with ParametersContext(command='sql db') as c:
    c.register_alias('database_name', ('--name', '-n'))
    c.register_alias('server_name', ('--server-name', '-s'))

with ParametersContext(command='sql db create') as c:
    c.register_alias('requested_service_objective_name', ('--service-objective-name',))
    c.register_alias('requested_service_objective_id', ('--service-objective-id',))
    # Alternative commands will be implemented for non-default create modes
    c.ignore('create_mode')
    # Source database id is only used for non-default create modes
    c.ignore('source_database_id')

## Data Warehouse will not be included in the first batch of GA commands
#with ParametersContext(command='sql db data-warehouse') as c:
#    c.register_alias('database_name', ('--database-name',))

with ParametersContext(command='sql db replication-link') as c:
    c.register_alias('database_name', ('--database-name', '-d'))

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

with ParametersContext(command='sql elastic-pool') as c:
    c.register_alias('elastic_pool_name', ('--name', '-n'))

with ParametersContext(command='sql elastic-pool db') as c:
    c.register_alias('elastic_pool_name', ('--elastic-pool-name',))
    c.register_alias('database_name', ('--name', '-n'))

## Recommended elastic pools will not be included in the first batch of GA commands
#with ParametersContext(command='sql elastic-pool recommended') as c:
#    c.register_alias('recommended_elastic_pool_name', ('--name', '-n'))

#with ParametersContext(command='sql elastic-pool recommended db') as c:
#    c.register_alias('recommended_elastic_pool_name', ('--recommended-elastic-pool-name',))
#    c.register_alias('database_name', ('--name', '-n'))

with ParametersContext(command='sql server') as c:
    c.register_alias('server_name', ('--name', '-n'))
    c.register_alias('administrator_login', ('--admin-login', '-u'))
    c.register_alias('administrator_login_password', ('--admin-password', '-p'))
    c.register_alias('version', ('--version-TODO-REMOVE-ME',))

with ParametersContext(command='sql server firewall') as c:
    c.register_alias('server_name', ('--server-name', '-s'))
    c.register_alias('firewall_rule_name', ('--name', '-n'))

with ParametersContext(command='sql server service-objective') as c:
    c.register_alias('server_name', ('--server-name',))
    c.register_alias('service_objective_name', ('--name', '-n'))

with ParametersContext(command='sql server create') as c:
    from azure.mgmt.sql.models.server import Server

    # About the patches:
    #
    # - Both administrator_login and administrator_login_password are required for server creation.
    # However these two parameters are given default value in the create_or_update function
    # signature, therefore, they can't be automatically converted to requirement arguments.
    c.expand('parameters', Server, group_name='Authentication', patches={
        'administrator_login': patch_arg_make_required,
        'administrator_login_password': patch_arg_make_required
    })

with ParametersContext(command='sql db create') as c:
    from azure.mgmt.sql.models.database import Database

    c.expand('parameters', Database)

with ParametersContext(command='sql elastic-pool create') as c:
    from azure.mgmt.sql.models.elastic_pool import ElasticPool

    c.expand('parameters', ElasticPool)
