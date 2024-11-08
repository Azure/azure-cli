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
from ._test_utils import CredentialReplacer, ConfigCredentialReplacer

class WebAppConnectionScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(WebAppConnectionScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer(), ConfigCredentialReplacer()]
        )

    @record_only()
    @unittest.skip('Needs passwordless extension released')
    def test_webapp_fabric_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'azure-service-connector',
            'site': 'DotNetAppSqlDb20240704',
            'database': 'clitest'
        })
        name = 'testfabricconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        connection_id = source_id + "/providers/Microsoft.ServiceLinker/linkers/" + name
        target_id = 'https://api.fabric.microsoft.com/v1/workspaces/13c65326-ecab-43f6-8a05-60927aaa4cec/SqlDatabases/4fdf6efe-23a9-4d74-8c4a-4ecc70c4d323'
        server = 'tcp:renzo-srv-6ae35870-c362-44b9-8389-ada214a46bb5-51240650dd56.database.windows.net,1433'
        database = 'AzureServiceConnectorTestSqlDb-4fdf6efe-23a9-4d74-8c4a-4ecc70c4d323'

        # prepare
        self.cmd('webapp identity remove --ids {}'.format(source_id))

        # create
        self.cmd('webapp connection create fabric-sql --connection {} --source-id {} --target-id {} \
                 --system-identity --client-type dotnet --opt-out publicnetwork \
                 --connstr-props "Server={}" \
                 "Database={}" '.format(name, source_id, target_id, server, database)
                )

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update
        self.cmd('webapp connection create fabric-sql --connection {} --source-id {} --target-id {} \
                 --system-identity --client-type python --opt-out publicnetwork \
                 --connstr-props "Server={}" "Database={}" '.format(name, source_id, target_id, server, database), 
                 checks = [ self.check('clientType', 'python')])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))

    @record_only()
    def test_webapp_appconfig_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-config-app',
            'config_store': 'servicelinker-app-configuration'
        })

        # prepare params        
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.AppConfig).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create appconfig --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python --customized-keys AZURE_APPCONFIGURATION_ENDPOINT=test_endpoint'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update appconfig --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        configs = self.cmd('webapp connection list-configuration --id {}'.format(connection_id)).get_output_in_json()
        self.assertTrue(any(x.get('name') == 'test_endpoint' for x in configs.get('configurations')))
        
        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_cosmoscassandra_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-cassandra-cosmos-asp-app',
            'account': 'servicelinker-cassandra-cosmos1',
            'key_space': 'coredb'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosCassandra).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-cassandra --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update cosmos-cassandra --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_cosmosgremlin_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-gremlin-cosmos-asp-app',
            'account': 'servicelinker-gremlin-cosmos',
            'database': 'coreDB',
            'graph': 'MyItem'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosGremlin).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-gremlin --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update cosmos-gremlin --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_cosmosmongo_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-mongo-cosmos-asp-app',
            'account': 'servicelinker-mongo-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosMongo).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-mongo --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type dotnet'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update cosmos-mongo --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))

    @record_only()
    def test_webapp_cosmossql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-sql-cosmos-asp-app',
            'account': 'servicelinker-sql-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosSql).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-sql --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update cosmos-sql --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_cosmostable_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-table-cosmos-asp-app',
            'account': 'servicelinker-table-cosmos',
            'table': 'MyItem'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosTable).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-table --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update cosmos-table --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_eventhub_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-eventhub-app',
            'namespace': 'servicelinkertesteventhub'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.EventHub).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create eventhub --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update eventhub --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_servicebus_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-servicebus-app',
            'namespace': 'servicelinkertestservicebus'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.ServiceBus).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create servicebus --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update servicebus --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_signalr_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-signalr-app',
            'signalr': 'servicelinker-signalr'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.SignalR).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create signalr --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type dotnet'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update signalr --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_webpubsub_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-webpubsub-app',
            'webpubsub': 'servicelinker-webpubsub'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.WebPubSub).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create webpubsub --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type dotnet'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update webpubsub --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_keyvault_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-keyvault-app',
            'vault': 'servicelinker-test-kv'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.KeyVault).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create keyvault --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update keyvault --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_postgresflexible_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-flexiblepostgresql-app',
            'server': 'servicelinker-flexiblepostgresql',
            'database': 'testdb'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.PostgresFlexible).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create postgres-flexible --connection {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update postgres-flexible --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(connection_id, user, password),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_redis_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-redis-app',
            'server': 'servicelinker-redis',
            'database': '0'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Redis).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create redis --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update redis --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_redisenterprise_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-redis-enterprise-app',
            'server': 'servicelinker-redis-enterprise',
            'database': 'default'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.RedisEnterprise).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create redis-enterprise --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update redis-enterprise --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_mysql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-mysql-app',
            'server': 'servicelinker-mysql',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Mysql).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create mysql --connection {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update mysql --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(connection_id, user, password),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))

    @record_only()
    def test_webapp_mysqlflexible_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-flexiblemysql-app',
            'server': 'servicelinker-flexible-mysql',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')
        keyvaultUri = "https://cupertino-kv-test.vault.azure.net/secrets/TestDbPassword"

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.MysqlFlexible).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create mysql-flexible --connection {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update mysql-flexible --id {} --client-type dotnet '
                 '--secret name={} secret-uri={}'.format(connection_id, user, keyvaultUri),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_postgres_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-postgresql-app',
            'server': 'servicelinker-postgresql',
            'database': 'testdb'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Postgres).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create postgres --connection {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update postgres --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(connection_id, user, password),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_sql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-sql-app',
            'server': 'servicelinker-sql',
            'database': 'handler-test'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Sql).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create sql --connection {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update sql --id {} --client-type dotnet '
                 '--secret name={} secret={}'.format(connection_id, user, password),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_sql_connection_string(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-sql-app',
            'server': 'servicelinker-sql',
            'database': 'handler-test'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Sql).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create sql --connection {} --source-id {} --target-id {} --secret name={} secret={} '
                 '--client-type dotnet --config-connstr'.format(name, source_id, target_id, user, password))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'dotnet-connectionString')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update sql --id {} --client-type dotnet --config-connstr '
                 '--secret name={} secret={}'.format(connection_id, user, password),
                 checks = [ self.check('clientType', 'dotnet-connectionString') ])

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_storageblob_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storageblob-app',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update storage-blob --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @live_only()
    # @unittest.skip('"run_cli_cmd" could only work at live mode, please comment it for live test')
    def test_webapp_storageblob_keyvault_ref(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storageblob-ref-app',
            'account': 'servicelinkerstorage',
            'vault': 'servicelinker-kv-ref',
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)
        keyvault_id = TARGET_RESOURCES.get(RESOURCE.KeyVault).format(**self.kwargs)

        # create connection
        id = self.cmd('webapp connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python --vault-id {}'.format(name, source_id, target_id, keyvault_id)).get_output_in_json().get('id')

        self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 2),
            ]
        )

        self.cmd(
            'webapp connection show --id {}'.format(id),
            checks = [
                self.check('secretStore.keyVaultId', keyvault_id),
                self.check('vNetSolution', None),
            ]
        )

        # update connection
        self.cmd('webapp connection update storage-blob --id {} '
                 '--secret'.format(id))

        self.cmd(
            'webapp connection show --id {}'.format(id),
            checks = [
                self.check('secretStore.keyVaultId', keyvault_id),
            ]
        )

        for conn in self.cmd('webapp connection list --source-id {}'.format(source_id)).get_output_in_json():
            self.cmd('webapp connection delete --id {} --yes'.format(conn.get('id')))


    @unittest.skip('Validation of network acls failure')
    def test_webapp_storageblob_vnet(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storage-app',
            'account': 'servicelinkerstorage',
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        output = self.cmd('webapp connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python --service-endpoint'.format(name, source_id, target_id)).get_output_in_json()

        id = output.get('id')
        self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
            ]
        )

        self.cmd(
            'webapp connection show --id {}'.format(id),
            checks = [
                self.check('vNetSolution.type', "serviceEndpoint"),
            ]
        )

        # update connection without vNetSolution
        result = self.cmd('webapp connection update storage-blob --id {} '
                 '--secret'.format(id)).get_output_in_json()

        update_result = self.cmd(
            'webapp connection show --id {}'.format(id),
            checks = [
                self.check('vNetSolution.type', "serviceEndpoint"),
            ]
        ).get_output_in_json()

        # update connection vnet solution
        self.cmd('webapp connection update storage-blob --id {} '
                 '--secret --service-endpoint false'.format(id))

        update_result = self.cmd(
            'webapp connection show --id {}'.format(id),
            checks = [
                self.check('vNetSolution', None),
            ]
        ).get_output_in_json()

        for conn in self.cmd('webapp connection list --source-id {}'.format(source_id)).get_output_in_json():
            self.cmd('webapp connection delete --id {} --yes'.format(conn.get('id')))

    # @record_only()
    @unittest.skip('Validation of network acls failure')
    def test_webapp_storageblob_vnet_pe(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storageblob-app',
            'account': 'servicelinkerteststorage',
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(
            RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        output = self.cmd('webapp connection create storage-blob --connection {} --source-id {} --target-id {} '
                          '--secret --client-type python --private-endpoint'.format(name, source_id, target_id)).get_output_in_json()

        id = output.get('id')
        self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks=[
                self.check('length(@)', 1),
            ]
        )

        self.cmd(
            'webapp connection show --id {}'.format(id),
            checks=[
                self.check('vNetSolution.type', "privateLink"),
            ]
        )

        # update connection without vNetSolution
        result = self.cmd('webapp connection update storage-blob --id {} '
                          '--secret'.format(id)).get_output_in_json()

        update_result = self.cmd(
            'webapp connection show --id {}'.format(id),
            checks=[
                self.check('vNetSolution.type', "privateLink"),
            ]
        ).get_output_in_json()

        # update connection vnet solution
        self.cmd('webapp connection update storage-blob --id {} '
                 '--secret --private-endpoint false'.format(id))

        update_result = self.cmd(
            'webapp connection show --id {}'.format(id),
            checks=[
                self.check('vNetSolution', None),
            ]
        ).get_output_in_json()

        for conn in self.cmd('webapp connection list --source-id {}'.format(source_id)).get_output_in_json():
            self.cmd(
                'webapp connection delete --id {} --yes'.format(conn.get('id')))


    @record_only()
    def test_webapp_storagequeue_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storagequeue-app',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageQueue).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-queue --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update storage-queue --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_storagefile_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storagefile-app',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageFile).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-file --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update storage-file --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_storagetable_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storagetable-app',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageTable).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-table --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update storage-table --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_confluentkafka_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-kafka-app',
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create confluent-cloud --connection {} --source-id {} '
                 '--bootstrap-server xxx.eastus.azure.confluent.cloud:9092 --kafka-key Name --kafka-secret Secret '
                 '--schema-registry https://xxx.eastus.azure.confluent.cloud --schema-key Name --schema-secret Secret '
                 '--client-type python'.format(name, source_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 2),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = [x.get('id') for x in connections if x.get('id').endswith(name)][0]
        # connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update confluent-cloud --connection {} '
                 '--source-id {} --client-type dotnet --kafka-secret Secret --customized-keys CONFLUENTCLOUD_KAFKA_BOOTSTRAPSERVER=test_server'.format(name, source_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        configs = self.cmd('webapp connection list-configuration --id {}'.format(connection_id)).get_output_in_json()
        self.assertTrue(any(x.get('name') == 'test_server' for x in configs.get('configurations')))
        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @live_only()
    # @unittest.skip('"run_cli_cmd" could only work at live mode, please comment it for live test')
    def test_webapp_confluentkafka_keyvault_ref(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-kafka-ref-app',
            'vault': 'servicelinker-kv-ref',
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        keyvault_id = TARGET_RESOURCES.get(RESOURCE.KeyVault).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create confluent-cloud --connection {} --source-id {} '
                 '--bootstrap-server xxx.eastus.azure.confluent.cloud:9092 --kafka-key Name --kafka-secret Secret '
                 '--schema-registry https://xxx.eastus.azure.confluent.cloud --schema-key Name --schema-secret Secret '
                 '--client-type python --vault-id {}'.format(name, source_id, keyvault_id))

        id = f'{source_id}/providers/Microsoft.ServiceLinker/linkers/{name}'

        self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 3),
            ]
        )

        self.cmd(
            'webapp connection show --id {}'.format(id),
            checks = [
                self.check('secretStore.keyVaultId', keyvault_id),
            ]
        )

        self.cmd(
            'webapp connection show --id {}_schema'.format(id),
            checks = [
                self.check('secretStore.keyVaultId', keyvault_id),
            ]
        )

        # update connection
        self.cmd('webapp connection update confluent-cloud --connection {} --source-id {} '
                 '--kafka-secret Secret'.format(name, source_id))

        self.cmd(
            'webapp connection show --id {}'.format(id),
            checks = [
                self.check('secretStore.keyVaultId', keyvault_id),
            ]
        )

        for conn in self.cmd('webapp connection list --source-id {}'.format(source_id)).get_output_in_json():
            self.cmd('webapp connection delete --id {} --yes'.format(conn.get('id')))

    @record_only()
    def test_webappslot_storageblob_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storageblob-app',
            'slot': 'slot1',
            'account': 'servicelinkerstorage'
        })

        # prepare params
        webAppSlotResourceIdFormat = '/subscriptions/{subscription}/resourceGroups/{source_resource_group}/providers/Microsoft.Web/sites/{site}/slots/{slot}'
        name = 'testconnslot1'
        source_id = webAppSlotResourceIdFormat.format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update storage-blob --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))

    @record_only()
    def test_webapp_app_insights_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'clitest',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-insight-app-euap',
            'appinsights': 'servicelinker-insight'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.AppInsights).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create app-insights --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update app-insights --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))

    @record_only()
    def test_webapp_storageblob_secret_opt_out_public_network_and_config(self):
        self._test_webapp_storageblob_secret_opt_out(['publicnetwork', 'configinfo'])
    
    @record_only()
    def test_webapp_storageblob_secret_opt_out_public_network(self):
        self._test_webapp_storageblob_secret_opt_out(['publicnetwork'])
    
    @record_only()
    def test_webapp_storageblob_secret_opt_out_config(self):
        self._test_webapp_storageblob_secret_opt_out(['configinfo'])

    def _test_webapp_storageblob_secret_opt_out(self, opt_out_list):

        def clear_firewall_rules():
            network = self.cmd(
                'storage account network-rule list '
                '--account-name {account} -g {target_resource_group}'.format(**self.kwargs)
                ).get_output_in_json()
            ip_rules = [ip_rule['ipAddressOrRange'] for ip_rule in network['ipRules']]
            self.cmd(
                'storage account network-rule remove '
                '--account-name {account} -g {target_resource_group} '
                '--ip-address {}'.format(' '.join(ip_rules), **self.kwargs))

        def validate_config(connection_id):
            # validate config
            # list configuration
            configurations = self.cmd(
                'webapp connection list-configuration --id {}'.format(connection_id)
            ).get_output_in_json()['configurations']
            if 'configinfo' in opt_out_list:
                self.assertEqual(len(configurations), 0)
            else:
                self.assertEqual(len(configurations), 1)

        def validate_firewall():
            network = self.cmd(
                'storage account network-rule list '
                '--account-name {account} -g {target_resource_group}'.format(**self.kwargs)
                ).get_output_in_json()
            if 'publicnetwork' in opt_out_list:
                self.assertEqual(len(network['ipRules']), 0)
            else:
                webapp = self.cmd(
                    'webapp show -g {source_resource_group} -n {site}'.format(**self.kwargs)
                ).get_output_in_json()
                ips = webapp['possibleOutboundIpAddresses']
                self.assertEqual(len(network['ipRules']), len(ips.split(',')))

        def validate_connection(connection_id):
            validate_config(connection_id)
            validate_firewall()

        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storageblob-app',
            'account': 'servicelinkerstorage'
        })     

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # clear firewall rules
        clear_firewall_rules()

        # create connection
        self.cmd('webapp connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--secret --client-type dotnet --opt-out {}'.format(name, source_id, 
                                                                     target_id, ' '.join(opt_out_list)))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        validate_connection(connection_id)
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # update connection
        self.cmd('webapp connection update storage-blob --id {} '
                 '--client-type python --opt-out {}'.format(connection_id,
                                                            ' '.join(opt_out_list)))

        validate_connection(connection_id)

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @live_only()
    # app config connection is different every time
    def test_webapp_storageblob_store_in_app_config(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'clitest',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-config-store-app-euap',
            'account': 'servicelinkerstorage',
            'config_store': 'servicelinker-appconfig-ref',
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)
        appconfig_id = TARGET_RESOURCES.get(RESOURCE.AppConfig).format(**self.kwargs)

        # create connection
        conn_id = self.cmd(
            'webapp connection create storage-blob '
            '--connection {} --source-id {} --target-id {} '
            '--secret --client-type python '
            '--appconfig-id {}'.format(name, source_id, target_id, appconfig_id)
        ).get_output_in_json().get('id')

        self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 2),
            ]
        )

        self.cmd(
            'webapp connection show --id {}'.format(conn_id),
            checks = [
                self.check('configurationInfo.configurationStore.appConfigurationId', appconfig_id)
            ]
        )

        configurations = self.cmd(
            'webapp connection list-configuration --id {}'.format(conn_id)
        ).get_output_in_json().get('configurations')

        # update connection
        self.cmd('webapp connection update storage-blob --id {} '
                 '--secret --client-type dotnet --appconfig-id {}'.format(conn_id, appconfig_id))

        for conn in self.cmd('webapp connection list --source-id {}'.format(source_id)).get_output_in_json():
            self.cmd('webapp connection delete --id {} --yes'.format(conn.get('id')))

    @record_only()
    def test_webapp_storage_blob_system_identity_opt_out_auth(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storageblob-app',
            'account': 'servicelinkerstorage'
        })     

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type dotnet --opt-out auth'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # validate connection, auth should not be validated
        self.cmd('webapp connection validate --id {}'.format(connection_id),
                 checks= [
                     self.check('length(@)', 3), # target existence, network and configinfo
                 ])
        # check system identity is not enabled
        validate_result = self.cmd('webapp identity show -g {} -n {}'.format(self.kwargs['source_resource_group'],
                                                                             self.kwargs['site']),
                 ).output
        self.assertEqual(validate_result, '')

        # update connection
        self.cmd('webapp connection update storage-blob --id {} '
                 '--client-type python --opt-out auth'.format(connection_id))
        # check system identity is not enabled
        validate_result = self.cmd('webapp identity show -g {} -n {}'.format(self.kwargs['source_resource_group'],
                                                                             self.kwargs['site']),
                 ).output
        self.assertEqual(validate_result, '')

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_storage_blob_null_auth(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'service-connector-int-test',
            'target_resource_group': 'service-connector-int-test',
            'site': 'servicelinker-optouttest-e2e',
            'account': 'servicelinkerinttest'
        })     

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-blob --connection {} --source-id {} --target-id {} '
                 '--opt-out auth configinfo'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo', 'None'),
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # validate connection, auth should not be validated
        self.cmd('webapp connection validate --id {}'.format(connection_id),
                 checks= [
                     self.check('length(@)', 2), # target existence, and network
                 ])
        # check system identity is not enabled
        validate_result = self.cmd('webapp identity show -g {} -n {}'.format(self.kwargs['source_resource_group'],
                                                                             self.kwargs['site']),
                 ).output
        if validate_result != '':
            self.cmd('role assignment list --assignee {}'.format(validate_result.get('principalId')),
                     checks=[
                         self.check('length(@)', 0)
                     ])

        # update connection with auth
        self.cmd('webapp connection update storage-blob --id {} '
                 '--system-identity'.format(connection_id))
        
        self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
            ]
        )

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_openai_secret_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'clitest',
            'target_resource_group': 'servicelinker-test-openai-group',
            'site': 'servicelinker-cognitive-app',
            'account': 'servicelinker-test-openai'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CognitiveServices).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cognitiveservices --connection {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update cognitiveservices --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))

    @record_only()
    def test_webapp_openai_system_identity_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'clitest',
            'target_resource_group': 'servicelinker-test-openai-group',
            'site': 'servicelinker-cognitive-app',
            'account': 'servicelinker-test-openai'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CognitiveServices).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cognitiveservices --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update cognitiveservices --id {} --client-type dotnet'.format(connection_id),
                 checks = [ 
                     self.check('clientType', 'dotnet'),
                     self.check('authInfo.authType', 'systemAssignedIdentity')
                ]
        )

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    def test_webapp_aiservices_system_identity_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'clitest',
            'target_resource_group': 'servicelinker-test-openai-group',
            'site': 'servicelinker-cognitive-app',
            'account': 'serivcelinker-aiservices-test'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CognitiveServices).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cognitiveservices --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update cognitiveservices --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))

    @record_only()
    def test_webapp_cognitive_services_system_identity_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'clitest',
            'target_resource_group': 'servicelinker-test-openai-group',
            'site': 'servicelinker-cognitive-app',
            'account': 'servicelinker-cognitiveservices-test'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.WebApp).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CognitiveServices).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cognitiveservices --connection {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'webapp connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update cognitiveservices --id {} --client-type dotnet'.format(connection_id),
                 checks = [ self.check('clientType', 'dotnet') ])

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))
