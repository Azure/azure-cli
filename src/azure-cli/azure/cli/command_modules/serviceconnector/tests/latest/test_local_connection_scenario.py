# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import unittest
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.testsdk import (
    ScenarioTest,
    record_only,
    live_only
)
from azure.cli.command_modules.serviceconnector._resource_config import (
    RESOURCE,
    SOURCE_RESOURCES,
    TARGET_RESOURCES
)
from azure.cli.testsdk.preparers import ResourceGroupPreparer
from ._test_utils import CredentialReplacer
resource_group = 'servicelinker-cli-test-group'


# @unittest.skip('Test with user account signed in')
class LocalConnectionScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(LocalConnectionScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer()]
        )


    def test_local_appconfig_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'config_store': 'servicelinker-app-configuration'
        })

        # prepare params
        name = 'testconn1'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.AppConfig).format(**self.kwargs)

        # create connection
        self.cmd('connection create appconfig -g {} --connection {} --target-id {} '
                 '--user-account --client-type python --customized-keys AZURE_APPCONFIGURATION_ENDPOINT=test_endpoint'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'userAccount'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update appconfig --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])
        # generate configuration
        configs = self.cmd('connection generate-configuration --id {}'.format(connection_id)).get_output_in_json()
        self.assertTrue(any(x.get('name') == 'test_endpoint' for x in configs.get('configurations')))
        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_cosmoscassandra_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-win-group',
            'account': 'servicelinker-cassandra-cosmos1',
            'key_space': 'coredb'
        })

        # prepare params
        name = 'testconn2'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.CosmosCassandra).format(**self.kwargs)

        # create connection
        self.cmd('connection create cosmos-cassandra -g {} --connection {} --target-id {} '
                 '--user-account --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'userAccount'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update cosmos-cassandra --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_cosmosgremlin_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-win-group',
            'account': 'servicelinker-gremlin-cosmos',
            'database': 'coreDB',
            'graph': 'MyItem'
        })

        # prepare params
        name = 'testconn3'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.CosmosGremlin).format(**self.kwargs)

        # create connection
        self.cmd('connection create cosmos-gremlin -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update cosmos-gremlin --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_cosmosmongo_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-win-group',
            'account': 'servicelinker-mongo-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn4'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.CosmosMongo).format(**self.kwargs)

        # create connection
        self.cmd('connection create cosmos-mongo -g {} --connection {} --target-id {} '
                 '--user-account --client-type dotnet'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'userAccount'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update cosmos-mongo --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_cosmossql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-win-group',
            'account': 'servicelinker-sql-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn5'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.CosmosSql).format(**self.kwargs)

        # create connection
        self.cmd('connection create cosmos-sql -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update cosmos-sql --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_cosmostable_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-win-group',
            'account': 'servicelinker-table-cosmos',
            'table': 'MyItem'
        })

        # prepare params
        name = 'testconn6'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.CosmosTable).format(**self.kwargs)

        # create connection
        self.cmd('connection create cosmos-table -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update cosmos-table --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_eventhub_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'namespace': 'servicelinkertesteventhub'
        })

        # prepare params
        name = 'testconn7'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.EventHub).format(**self.kwargs)

        # create connection
        self.cmd('connection create eventhub -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update eventhub --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_servicebus_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'namespace': 'servicelinkertestservicebus'
        })

        # prepare params
        name = 'testconn8'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.ServiceBus).format(**self.kwargs)

        # create connection
        self.cmd('connection create servicebus -g {} --connection {} --target-id {} '
                 '--user-account --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'userAccount'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update servicebus --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_signalr_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'signalr': 'servicelinker-signalr'
        })

        # prepare params
        name = 'testconn9'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.SignalR).format(**self.kwargs)

        # create connection
        self.cmd('connection create signalr -g {} --connection {} --target-id {} '
                 '--secret --client-type dotnet'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update signalr --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_webpubsub_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'webpubsub': 'servicelinker-webpubsub'
        })

        # prepare params
        name = 'testconn10'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.WebPubSub).format(**self.kwargs)

        # create connection
        self.cmd('connection create webpubsub -g {} --connection {} --target-id {} '
                 '--secret --client-type dotnet'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update webpubsub --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_keyvault_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'vault': 'servicelinker-test-kv'
        })

        # prepare params
        name = 'testconn11'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.KeyVault).format(**self.kwargs)

        # create connection
        self.cmd('connection create keyvault -g {} --connection {} --target-id {} '
                 '--client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'userAccount'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update keyvault --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_postgresflexible_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'server': 'servicelinker-flexiblepostgresql',
            'database': 'test'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn12'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.PostgresFlexible).format(**self.kwargs)

        # create connection
        self.cmd('connection create postgres-flexible -g {} --connection {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(resource_group, name, target_id, user, password))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update postgres-flexible --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(
                     connection_id, user, password),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_redis_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'server': 'servicelinker-redis',
            'database': '0'
        })

        # prepare params
        name = 'testconn13'
        target_id = TARGET_RESOURCES.get(RESOURCE.Redis).format(**self.kwargs)

        # create connection
        self.cmd('connection create redis -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update redis --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_redisenterprise_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'server': 'servicelinker-redis-enterprise',
            'database': 'default'
        })

        # prepare params
        name = 'testconn14'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.RedisEnterprise).format(**self.kwargs)

        # create connection
        self.cmd('connection create redis-enterprise -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update redis-enterprise --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_mysql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'server': 'servicelinker-mysql',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn15'
        target_id = TARGET_RESOURCES.get(RESOURCE.Mysql).format(**self.kwargs)

        # create connection
        self.cmd('connection create mysql -g {} --connection {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(resource_group, name, target_id, user, password))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update mysql --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(
                     connection_id, user, password),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_mysqlflexible_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'server': 'servicelinker-flexible-mysql',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')
        keyvaultUri = "https://cupertino-kv-test.vault.azure.net/secrets/TestDbPassword"

        # prepare params
        name = 'testconn16'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.MysqlFlexible).format(**self.kwargs)

        # create connection
        self.cmd('connection create mysql-flexible -g {} --connection {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(resource_group, name, target_id, user, password))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update mysql-flexible --id {} --client-type dotnet '
                 '--secret name={} secret-uri={}'.format(
                     connection_id, user, keyvaultUri),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_postgres_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'server': 'servicelinker-postgresql',
            'database': 'test'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn17'
        target_id = TARGET_RESOURCES.get(
            RESOURCE.Postgres).format(**self.kwargs)

        # create connection
        self.cmd('connection create postgres -g {} --connection {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(resource_group, name, target_id, user, password))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update postgres --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(
                     connection_id, user, password),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_sql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'server': 'servicelinker-sql',
            'database': 'handler-test'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn18'
        target_id = TARGET_RESOURCES.get(RESOURCE.Sql).format(**self.kwargs)

        # create connection
        self.cmd('connection create sql -g {} --connection {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(resource_group, name, target_id, user, password))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update sql --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(
                     connection_id, user, password),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_storageblob_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn20'

        target_id = TARGET_RESOURCES.get(
            RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        self.cmd('connection create storage-blob -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update storage-blob -g {} --id {} --client-type dotnet'.format(resource_group, connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))

    @live_only()
    @unittest.skip('keyvault ref not supported')
    def test_local_storageblob_keyvault_ref(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'account': 'servicelinkerstorage',
            'vault': 'servicelinker-kv-ref',
        })

        # prepare params
        name = 'testconn21'

        target_id = TARGET_RESOURCES.get(
            RESOURCE.StorageBlob).format(**self.kwargs)
        keyvault_id = TARGET_RESOURCES.get(
            RESOURCE.KeyVault).format(**self.kwargs)

        # create connection
        id = self.cmd('connection create storage-blob -g {} --connection {} --target-id {} '
                      '--secret --client-type python --vault-id {}'.format(resource_group, name, target_id, keyvault_id)).get_output_in_json().get('id')

        self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 2),
            ]
        )

        self.cmd(
            'connection show --id {}'.format(id),
            checks=[
                self.check('secretStore.keyVaultId', keyvault_id),
                self.check('vNetSolution', None),
            ]
        )

        # update connection
        self.cmd('connection update storage-blob --id {} '
                 '--secret'.format(id))

        self.cmd(
            'connection show --id {}'.format(id),
            checks=[
                self.check('secretStore.keyVaultId', keyvault_id),
            ]
        )

        for conn in self.cmd('connection list -g {}'.format(resource_group)).get_output_in_json():
            self.cmd('connection delete --id {} --yes'.format(conn.get('id')))


    def test_local_storagequeue_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn24'

        target_id = TARGET_RESOURCES.get(
            RESOURCE.StorageQueue).format(**self.kwargs)

        # create connection
        self.cmd('connection create storage-queue -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update storage-queue --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_storagefile_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn25'

        target_id = TARGET_RESOURCES.get(
            RESOURCE.StorageFile).format(**self.kwargs)

        # create connection
        self.cmd('connection create storage-file -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update storage-file --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))


    def test_local_storagetable_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn26'

        target_id = TARGET_RESOURCES.get(
            RESOURCE.StorageTable).format(**self.kwargs)

        # create connection
        self.cmd('connection create storage-table -g {} --connection {} --target-id {} '
                 '--secret --client-type python'.format(resource_group, name, target_id))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update storage-table --id {} --client-type dotnet'.format(connection_id),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        self.cmd('connection generate-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))

    
    def test_local_confluentkafka_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
        })

        # prepare params
        name = 'testconn27'

        # create connection
        self.cmd('connection create confluent-cloud -g {} --connection {} '
                 '--bootstrap-server xxx.eastus.azure.confluent.cloud:9092 --kafka-key Name --kafka-secret Secret '
                 '--schema-registry https://xxx.eastus.azure.confluent.cloud --schema-key Name --schema-secret Secret '
                 '--client-type python '.format(resource_group, name))

        # list connection
        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 2),
                # self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('connection update confluent-cloud -g {} --connection {} '
                 '--client-type dotnet --kafka-secret Secret --customized-keys CONFLUENTCLOUD_KAFKA_BOOTSTRAPSERVER=test_server'.format(resource_group, name),
                 checks=[self.check('clientType', 'dotnet')])

        # generate configuration
        configs = self.cmd('connection generate-configuration --id {}'.format(connection_id)).get_output_in_json()
        self.assertTrue(any(x.get('name') == 'test_server' for x in configs.get('configurations')))
        # validate connection
        self.cmd('connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('connection delete --id {} --yes'.format(connection_id))

    def test_local_connection_list_support_types(self):
        self.cmd(
            'connection list-support-types'.format(resource_group),
            checks=[
                self.check('length(@)', 23),
            ]
        ).get_output_in_json()

    def test_local_connection_preview_configuration(self):
        self.cmd(
            'connection preview-configuration appconfig --client-type dotnet',
            checks=[
                self.check('length(@)', 6),
            ]
        ).get_output_in_json()


    @unittest.skip('Keyvault reference not supported')
    def test_local_confluentkafka_keyvault_ref(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'target_resource_group': 'servicelinker-test-linux-group',
            'vault': 'servicelinker-kv-ref',
        })

        # prepare params
        name = 'testconn28'

        keyvault_id = TARGET_RESOURCES.get(
            RESOURCE.KeyVault).format(**self.kwargs)

        # create connection
        self.cmd('connection create confluent-cloud -g {} --connection {} '
                 '--bootstrap-server xxx.eastus.azure.confluent.cloud:9092 --kafka-key Name --kafka-secret Secret '
                 '--schema-registry https://xxx.eastus.azure.confluent.cloud --schema-key Name --schema-secret Secret '
                 '--client-type python --vault-id {}'.format(resource_group, name, keyvault_id))

        connections = self.cmd(
            'connection list -g {}'.format(resource_group),
            checks=[
                self.check('length(@)', 3),
            ]
        ).get_output_in_json()

        id = connections[0].get('id')

        self.cmd(
            'connection show --id {}'.format(id),
            checks=[
                self.check('secretStore.keyVaultId', keyvault_id),
            ]
        )

        self.cmd(
            'connection show --id {}_schema'.format(id),
            checks=[
                self.check('secretStore.keyVaultId', keyvault_id),
            ]
        )

        # update connection
        self.cmd('connection update confluent-cloud -g {} --connection {} '
                 '--kafka-secret Secret'.format(resource_group, name))

        self.cmd(
            'connection show --id {}'.format(id),
            checks=[
                self.check('secretStore.keyVaultId', keyvault_id),
            ]
        )

        for conn in self.cmd('connection list -g {}'.format(resource_group)).get_output_in_json():
            self.cmd('connection delete --id {} --yes'.format(conn.get('id')))
