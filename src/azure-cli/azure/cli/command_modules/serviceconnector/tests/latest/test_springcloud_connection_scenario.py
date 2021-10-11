# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import unittest

from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.testsdk import (
    ScenarioTest,
    record_only
)
from azure_devtools.scenario_tests import RecordingProcessor
from azure_devtools.scenario_tests.utilities import is_text_payload
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

        if is_text_payload(request) and request.body and json.loads(request.body):
            body = self.recursive_hide(json.loads(request.body))
            request.body = json.dumps(body)
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


@unittest.skip('Need spring-cloud extension installed')
class SpringCloudConnectionScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(SpringCloudConnectionScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer()]
        )

    # @record_only
    def test_springcloud_appconfig_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'appconfiguration',
            'deployment': 'default',
            'config_store': 'servicelinker-app-configuration'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.AppConfig).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create appconfig --name {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_cosmoscassandra_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmoscassandra',
            'deployment': 'default',
            'account': 'servicelinker-cassandra-cosmos',
            'key_space': 'coredb'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosCassandra).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create cosmos-cassandra --name {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_cosmosgremlin_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmosgremlin',
            'deployment': 'default',
            'account': 'servicelinker-gremlin-cosmos',
            'database': 'coreDB',
            'graph': 'MyItem'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosGremlin).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create cosmos-gremlin --name {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_cosmosmongo_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmosmongo',
            'deployment': 'default',
            'account': 'servicelinker-mongo-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosMongo).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create cosmos-mongo --name {} --source-id {} --target-id {} '
                 '--system-identity --client-type dotnet'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_cosmossql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmossql',
            'deployment': 'default',
            'account': 'servicelinker-sql-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosSql).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create cosmos-sql --name {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_cosmostable_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmostable',
            'deployment': 'default',
            'account': 'servicelinker-table-cosmos',
            'table': 'MyItem'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosTable).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create cosmos-table --name {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_eventhub_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'eventhub',
            'deployment': 'default',
            'namespace': 'servicelinkertesteventhub' 
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.EventHub).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create eventhub --name {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_postgresflexible_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'postgresflexible',
            'deployment': 'default',
            'server': 'servicelinker-flexiblepostgresql',
            'database': 'postgres'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.PostgresFlexible).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create postgres-flexible --name {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_keyvault_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'keyvaultmi',
            'deployment': 'default',
            'vault': 'servicelinker-test-kv'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.KeyVault).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create keyvault --name {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_mysql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'mysql',
            'deployment': 'default',
            'server': 'servicelinker-mysql',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Mysql).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create mysql --name {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_mysqlflexible_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'mysqlflexible',
            'deployment': 'default',
            'server': 'servicelinker-flexible-mysql',
            'database': 'mysqlDB'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.MysqlFlexible).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create mysql-flexible --name {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_postgres_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'postgresql',
            'deployment': 'default',
            'server': 'servicelinker-postgresql',
            'database': 'postgres'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Postgres).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create postgres --name {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_sql_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'sqldb',
            'deployment': 'default',
            'server': 'servicelinker-sql',
            'database': 'handler-test'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.Sql).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create sql --name {} --source-id {} --target-id {} '
                 '--secret name={} secret={} --client-type python'.format(name, source_id, target_id, user, password))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_storageblob_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'storageblob',
            'deployment': 'default',
            'account': 'servicelinkerteststorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create storage-blob --name {} --source-id {} --target-id {} '
                 '--system-identity --client-type python'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))
    

    # @record_only
    def test_springcloud_storagequeue_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'storagequeue',
            'deployment': 'default',
            'account': 'servicelinkerteststorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageQueue).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create storage-queue --name {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))
        
        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_storagefile_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'storagefile',
            'deployment': 'default',
            'account': 'servicelinkerteststorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageFile).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create storage-file --name {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))


    # @record_only
    def test_springcloud_storagetable_e2e(self):
        self.kwargs.update({
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'storagetable',
            'deployment': 'default',
            'account': 'servicelinkerteststorage'
        })

        # prepare params
        name = 'testconn'
        source_id = SOURCE_RESOURCES.get(RESOURCE.SpringCloud).format(**self.kwargs)
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageTable).format(**self.kwargs)

        # create connection
        self.cmd('spring-cloud connection create storage-table --name {} --source-id {} --target-id {} '
                 '--secret --client-type python'.format(name, source_id, target_id))

        # list connection
        connections = self.cmd(
            'spring-cloud connection list --source-id {}'.format(source_id),
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --id {}'.format(connection_id))

        # validate connection
        self.cmd('spring-cloud connection validate --id {}'.format(connection_id))

        # show connection
        self.cmd('spring-cloud connection show --id {}'.format(connection_id))

        # delete connection
        self.cmd('spring-cloud connection delete --id {} --yes'.format(connection_id))
