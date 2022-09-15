# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import unittest
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.testsdk import (
    ScenarioTest,
    live_only
)
from azure.cli.command_modules.serviceconnector._resource_config import (
    RESOURCE,
    SOURCE_RESOURCES,
    TARGET_RESOURCES
)
from ._test_utils import CredentialReplacer

@unittest.skip('Need environment prepared')
class PasswordlessConnectionScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(PasswordlessConnectionScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer()]
        )

    def test_aad_webapp_sql(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'zxf-test',
            'target_resource_group': 'zxf-test',
            'site': 'xf-mi-test',
            'server': 'servicelinker-sql-mi',
            'database': 'clitest'
        })
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Sql).format(**self.kwargs)
        connection_id = source_id + "/providers/Microsoft.ServiceLinker/linkers/" + name

        # prepare
        self.cmd('webapp identity remove --ids {}'.format(source_id))
        self.cmd('sql server update -e false --ids {}'.format(target_id))
        self.cmd('sql db create -g {target_resource_group} -s {server} -n {database}')

        # create
        self.cmd('webapp connection create sql --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type dotnet'.format(name, source_id, target_id))
        # clean
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))

        # recreate and test
        self.cmd('webapp connection create sql --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type dotnet'.format(name, source_id, target_id))
        # clean
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))
        self.cmd('sql db delete -y -g {target_resource_group} -s {server} -n {database}')

    def test_aad_spring_mysqlflexible(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'zxf-test',
            'spring': 'springeuap',
            'app': 'mysqlflexmi',
            'deployment': 'default',
            'server': 'xf-mysqlflex-test',
            'database': 'mysqlDB',
        })
        mysql_identity_id = '/subscriptions/d82d7763-8e12-4f39-a7b6-496a983ec2f4/resourcegroups/zxf-test/providers/Microsoft.ManagedIdentity/userAssignedIdentities/servicelinker-aad-umi'

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.MysqlFlexible).format(**self.kwargs)
        connection_id = source_id + "/providers/Microsoft.ServiceLinker/linkers/" + name

        # prepare
        self.cmd('spring app identity remove -n {app} -s {spring} -g {source_resource_group} --system-assigned')
        self.cmd('mysql flexible-server ad-admin delete -g {target_resource_group} -s {server} -y')
        self.cmd('mysql flexible-server db create -g {target_resource_group} --server-name {server} --database-name {database}')
        # self.cmd('mysql flexible-server identity remove -g {target_resource_group} -s {server} -y --identity ' + mysql_identity_id)

        # create connection
        self.cmd('spring connection create mysql-flexible --connection {} --source-id {} --target-id {} '
                 '--client-type springboot --system-identity mysql-identity-id={}'.format(name, source_id, target_id, mysql_identity_id))
        # delete connection
        self.cmd('spring connection delete --id {} --yes'.format(connection_id))


        # create connection
        self.cmd('spring connection create mysql-flexible --connection {} --source-id {} --target-id {} '
                 '--client-type springboot --system-identity mysql-identity-id={}'.format(name, source_id, target_id, mysql_identity_id))
        # delete connection
        self.cmd('spring connection delete --id {} --yes'.format(connection_id))
        self.cmd('mysql flexible-server db delete -y -g {target_resource_group} --server-name {server} --database-name {database}')

    def test_aad_containerapp_postgresflexible(self):
        default_container_name = 'simple-hello-world-container'
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'zxf-test',
            'target_resource_group': 'zxf-test',
            'app': 'servicelinker-mysql-aca',
            'server': 'xf-pgflex-clitest',
            'database': 'testdb1',
            'containerapp_env': '/subscriptions/d82d7763-8e12-4f39-a7b6-496a983ec2f4/resourceGroups/container-app/providers/Microsoft.App/managedEnvironments/north-europe'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.ContainerApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.PostgresFlexible).format(**self.kwargs)
        connection_id = source_id + "/providers/Microsoft.ServiceLinker/linkers/" + name

        # prepare
        self.cmd('containerapp delete -n {app} -g {source_resource_group}')
        self.cmd('containerapp create -n {app} -g {source_resource_group} --environment {containerapp_env} --image nginx')
        self.cmd('postgres flexible-server delete -y -g {target_resource_group} -n {server}')
        self.cmd('postgres flexible-server create -y -g {target_resource_group} -n {server}')
        self.cmd('postgres flexible-server db create -g {target_resource_group} -s {server} -d {database}')

        # create
        self.cmd('containerapp connection create postgres-flexible --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type springboot -c {}'.format(name, source_id, target_id, default_container_name))
        configs = self.cmd('containerapp connection list-configuration --id {}'.format(connection_id)).get_output_in_json();
        # clean
        self.cmd('containerapp connection delete --id {} --yes'.format(connection_id))
        #
        # # recreate and test
        # self.cmd('containerapp connection create postgres-flexible --connection {} --source-id {} --target-id {} '
        #          '--system-identity --client-type dotnet -c {}'.format(name, source_id, target_id, default_container_name))
        # clean
        # self.cmd('containerapp connection delete --id {} --yes'.format(connection_id))
        # self.cmd('postgres flexible-server delete -y -g {target_resource_group} -n {server}')


    def test_aad_webapp_postgressingle(self):
        self.kwargs.update({
            'subscription': "d82d7763-8e12-4f39-a7b6-496a983ec2f4",
            'source_resource_group': 'zxf-test',
            'target_resource_group': 'zxf-test',
            'site': 'xf-pg-app',
            'server': 'xfpostgre',
            'database': 'testdb'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.PostgresFlexible).format(**self.kwargs)
        connection_id = source_id + "/providers/Microsoft.ServiceLinker/linkers/" + name

        # prepare
        self.cmd('webapp identity remove --ids {}'.format(source_id))
        # self.cmd('postgres server delete -y -g {target_resource_group} -n {server}')
        # self.cmd('postgres server create -y -g {target_resource_group} -n {server}')
        self.cmd('postgres db delete -g {target_resource_group} -s {server} -n {database}')
        self.cmd('postgres db create -g {target_resource_group} -s {server} -n {database}')

        # create
        self.cmd('webapp connection create postgres-flexible --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type springboot'.format(name, source_id, target_id))
        configs = self.cmd('webapp connection list-configuration --id {}'.format(connection_id)).get_output_in_json();

