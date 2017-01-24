# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import ParametersContext, patch_arg_make_required


with ParametersContext(command='sql db') as c:
    c.register_alias('database_name', ('--name', '-n'))

with ParametersContext(command='sql db data-warehouse') as c:
    c.register_alias('database_name', ('--database-name',))

with ParametersContext(command='sql db replication-link') as c:
    c.register_alias('database_name', ('--database-name',))

with ParametersContext(command='sql db restore-point') as c:
    c.register_alias('database_name', ('--database-name',))

with ParametersContext(command='sql db service-tier-advisor') as c:
    c.register_alias('database_name', ('--database-name',))

with ParametersContext(command='sql db transparent-data-encryption') as c:
    c.register_alias('database_name', ('--database-name',))

with ParametersContext(command='sql elastic-pools') as c:
    c.register_alias('elastic_pool_name', ('--name', '-n'))

with ParametersContext(command='sql elastic-pools db') as c:
    c.register_alias('elastic_pool_name', ('--elastic-pool-name',))
    c.register_alias('database_name', ('--name', '-n'))

with ParametersContext(command='sql elastic-pools recommended') as c:
    c.register_alias('recommended_elastic_pool_name', ('--name', '-n'))

with ParametersContext(command='sql elastic-pools recommended db') as c:
    c.register_alias('recommended_elastic_pool_name', ('--recommended-elastic-pool-name',))
    c.register_alias('database_name', ('--name', '-n'))

with ParametersContext(command='sql server') as c:
    c.register_alias('server_name', ('--name', '-n'))

with ParametersContext(command='sql server firewall') as c:
    c.register_alias('server_name', ('--server-name',))
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

with ParametersContext(command='sql elastic-pools create') as c:
    from azure.mgmt.sql.models.elastic_pool import ElasticPool

    c.expand('parameters', ElasticPool)
