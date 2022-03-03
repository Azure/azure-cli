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
from azure.cli.testsdk.scenario_tests import RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_text_payload
from azure.cli.command_modules.serviceconnector._resource_config import (
    RESOURCE,
    SOURCE_RESOURCES,
    TARGET_RESOURCES
)


class CredentialReplacer(RecordingProcessor):

    def recursive_hide(self, props):
        # hide sensitive data recursively
        fake_content = 'hidden'
        sensitive_data = ['password=', 'key=']

        if isinstance(props, dict):
            for key, val in props.items():
                props[key] = self.recursive_hide(val)
        elif isinstance(props, list):
            for index, val in enumerate(props):
                props[index] = self.recursive_hide(val)
        elif isinstance(props, str):
            for data in sensitive_data:
                if data in props.lower():
                    props = fake_content

        return props

    def process_request(self, request):
        import json

        # hide secrets in request body
        if is_text_payload(request) and request.body and json.loads(request.body):
            body = self.recursive_hide(json.loads(request.body))
            request.body = json.dumps(body)

        # hide token in header
        if 'x-ms-cupertino-test-token' in request.headers:
            request.headers['x-ms-cupertino-test-token'] = 'hidden'
        if 'x-ms-serviceconnector-user-token' in request.headers:
            request.headers['x-ms-serviceconnector-user-token'] = 'hidden'
        
        return request

    def process_response(self, response):
        import json

        if is_text_payload(response) and response['body']['string']:
            try:
                body = json.loads(response['body']['string'])
                body = self.recursive_hide(body)
                response['body']['string'] = json.dumps(body)
            except Exception:
                pass

        return response


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
            'site': 'servicelinker-config-app2',
            'config_store': 'servicelinker-app-configuration2'
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
            'site': 'servicelinker-cassandra-cosmos-asp-app2',
            'account': 'servicelinker-cassandra-cosmos2',
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
            'site': 'servicelinker-gremlin-cosmos-asp-app2',
            'account': 'servicelinker-gremlin-cosmos2',
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
            'site': 'servicelinker-mongo-cosmos-asp-app2',
            'account': 'servicelinker-mongo-cosmos2',
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
            'site': 'servicelinker-sql-cosmos-asp-app2',
            'account': 'servicelinker-sql-cosmos2',
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
            'site': 'servicelinker-table-cosmos-asp-app2',
            'account': 'servicelinker-table-cosmos2',
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
            'site': 'servicelinker-eventhub-app2',
            'namespace': 'servicelinkertesteventhub2' 
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
            'site': 'servicelinker-servicebus-app2',
            'namespace': 'servicelinkertestservicebus2' 
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
            'site': 'servicelinker-signalr-app2',
            'signalr': 'servicelinker-signalr2' 
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
            'site': 'servicelinker-keyvault-app2',
            'vault': 'servicelinker-test-kv2'
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
            'site': 'servicelinker-flexiblepostgresql-app2',
            'server': 'servicelinker-flexiblepostgresql2',
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

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    @unittest.skip('Temporarily removed from supported target resources')
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

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    @unittest.skip('Temporarily removed from supported target resources')
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
            'site': 'servicelinker-mysql-app2',
            'server': 'servicelinker-mysql2',
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
            'site': 'servicelinker-flexiblemysql-app2',
            'server': 'servicelinker-flexible-mysql2',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

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
            'site': 'servicelinker-postgresql-app2',
            'server': 'servicelinker-postgresql2',
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

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @record_only()
    @unittest.skip('Temporarily removed from supported target resources')
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
            'site': 'servicelinker-storageblob-app2',
            'account': 'servicelinkerstorage2'
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

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @live_only()
    @unittest.skip('"run_cli_cmd" could only work at live mode, please comment it for live test')
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
    def test_webapp_storagequeue_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storagequeue-app2',
            'account': 'servicelinkerstorage2'
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
            'site': 'servicelinker-storagefile-app2',
            'account': 'servicelinkerstorage2'
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
            'site': 'servicelinker-storagetable-app2',
            'account': 'servicelinkerstorage2'
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
            'site': 'servicelinker-kafka-app2',
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

        # list configuration
        self.cmd('webapp connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('webapp connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('webapp connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    @live_only()
    @unittest.skip('"run_cli_cmd" could only work at live mode, please comment it for live test')
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
