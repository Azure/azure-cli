# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

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
from ._test_utils import CredentialReplacer

class WebAppConnectionScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(WebAppConnectionScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer()]
        )

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
        self.cmd('webapp connection update appconfig --id {} --client-type dotnet'.format(connection_id),
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
    def test_webapp_cosmoscassandra_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-cassandra-cosmos-asp-app',
            'account': 'servicelinker-cassandra-cosmos',
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
            'database': 'test'
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
                 '--secret name={} keyVaultSecretUri={}'.format(connection_id, user, keyvaultUri),
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
            'database': 'test'
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


    @record_only()
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
        connection_id = connections[0].get('id')

        # update connection
        self.cmd('webapp connection update confluent-cloud --connection {} '
                 '--source-id {} --client-type dotnet --kafka-secret Secret'.format(name, source_id),
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
