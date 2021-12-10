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

@unittest.skip('')
class WebAppConnectionWithoutIdScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(WebAppConnectionWithoutIdScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer()]
        )

    # @record_only()
    def test_webapp_appconfig_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-config-app',
            'config_store': 'servicelinker-app-configuration'
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.AppConfig).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create appconfig --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --app-config {config_store} --system-identity --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_cosmoscassandra_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-cassandra-cosmos-asp-app',
            'account': 'servicelinker-cassandra-cosmos',
            'key_space': 'coredb'
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosCassandra).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-cassandra --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --account {account} --key-space {key_space} --system-identity --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_cosmosgremlin_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
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
        
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosGremlin).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-gremlin --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --account {account} --database {database} --graph {graph} --system-identity --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_cosmosmongo_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-mongo-cosmos-asp-app',
            'account': 'servicelinker-mongo-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosMongo).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-mongo --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --account {account} --database {database} --system-identity --client-type dotnet')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'dotnet')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_cosmossql_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-sql-cosmos-asp-app',
            'account': 'servicelinker-sql-cosmos',
            'database': 'coreDB'
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosSql).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-sql --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --account {account} --database {database} --system-identity --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_cosmostable_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-win-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'site': 'servicelinker-table-cosmos-asp-app',
            'account': 'servicelinker-table-cosmos',
            'table': 'MyItem'
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.CosmosTable).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create cosmos-table --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --account {account} --table {table} --system-identity --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_eventhub_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-eventhub-app',
            'namespace': 'servicelinkertesteventhub' 
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.EventHub).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create eventhub --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --namespace {namespace} --system-identity --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_postgresflexible_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-flexiblepostgresql-app',
            'server': 'servicelinker-flexiblepostgresql',
            'database': 'postgres'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')
        self.kwargs.update({
            'user': user,
            'password': password
        })
        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.PostgresFlexible).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create postgres-flexible --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_keyvault_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-keyvault-app',
            'vault': 'servicelinker-test-kv'
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.KeyVault).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create keyvault --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --vault {vault} --system-identity --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_mysql_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
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
        self.kwargs.update({
            'user': user,
            'password': password
        })
        
        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.Mysql).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create mysql --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type python'.format(user, password))
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_mysqlflexible_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
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
        self.kwargs.update({
            'user': user,
            'password': password
        })
        
        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.MysqlFlexible).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create mysql-flexible --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type python'.format(user, password))
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_postgres_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-postgresql-app',
            'server': 'servicelinker-postgresql',
            'database': 'postgres'
        })

        # prepare password
        user = 'servicelinker'
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')
        self.kwargs.update({
            'user': user,
            'password': password
        })
        
        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.Postgres).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create postgres --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type python'.format(user, password))
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_sql_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
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
        self.kwargs.update({
            'user': user,
            'password': password
        })
        
        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.Sql).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create sql --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type python'.format(user, password))
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_storageblob_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storageblob-app',
            'account': 'servicelinkerteststorage'
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageBlob).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-blob --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --account {account} --system-identity --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))
    

    # @record_only()
    def test_webapp_storagequeue_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storagequeue-app',
            'account': 'servicelinkerteststorage'
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageQueue).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-queue --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --account {account} --secret --client-type python')
        
        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_storagefile_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storagefile-app',
            'account': 'servicelinkerteststorage'
        })

        # prepare params
        name = 'testconn'
        
        

        # create connection
        self.cmd('webapp connection create storage-file --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --account {account} --secret --client-type python')

        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))


    # @record_only()
    def test_webapp_storagetable_e2e(self):
        self.kwargs.update({
            'name': 'testconn1',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'site': 'servicelinker-storagetable-app',
            'account': 'servicelinkerteststorage'
        })

        # prepare params
        name = 'testconn'
        
        target_id = TARGET_RESOURCES.get(RESOURCE.StorageTable).format(**self.kwargs)

        # create connection
        self.cmd('webapp connection create storage-table --connection {name} -g {source_resource_group} -n {site} '
                 '--tg {target_resource_group} --account {account} --secret --client-type python')

        # list connection
        connections = self.cmd(
            'webapp connection list -g {source_resource_group} -n {site}',
            checks = [
                self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'python')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('webapp connection list-configuration --connection {name} -g {source_resource_group} -n {site}')

        # validate connection
        self.cmd('webapp connection validate --connection {name} -g {source_resource_group} -n {site}')

        # show connection
        self.cmd('webapp connection show --connection {name} -g {source_resource_group} -n {site}')

        # delete connection
        self.cmd('webapp connection delete --id {} --yes'.format(connection_id))
