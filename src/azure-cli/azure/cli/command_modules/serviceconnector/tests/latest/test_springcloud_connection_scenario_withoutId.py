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


@unittest.skip('Need spring-cloud extension installed')
class SpringCloudConnectionWithoutIdScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(SpringCloudConnectionWithoutIdScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer()]
        )

    # @record_only
    def test_springcloud_appconfig_e2e(self):
        self.kwargs.update({
            'name' : 'testconn5',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'appconfiguration',
            'deployment': 'default',
            'config_store': 'servicelinker-app-configuration'
        })

        # create connection
        self.cmd('spring-cloud connection create appconfig --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --app-config {config_store} --system-identity --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app} ',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_cosmoscassandra_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmoscassandra',
            'deployment': 'default',
            'account': 'servicelinker-cassandra-cosmos',
            'key_space': 'coredb'
        })


        # create connection
        self.cmd('spring-cloud connection create cosmos-cassandra --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --account {account} --key-space {key_space} --system-identity --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_cosmosgremlin_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmosgremlin',
            'deployment': 'default',
            'account': 'servicelinker-gremlin-cosmos',
            'database': 'coreDB',
            'graph': 'MyItem'
        })


        # create connection
        self.cmd('spring-cloud connection create cosmos-gremlin --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --account {account} --database {database} --graph {graph} --system-identity --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_cosmosmongo_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmosmongo',
            'deployment': 'default',
            'account': 'servicelinker-mongo-cosmos',
            'database': 'coreDB'
        })


        # create connection
        self.cmd('spring-cloud connection create cosmos-mongo --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --account {account} --database {database} --system-identity --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_cosmossql_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmossql',
            'deployment': 'default',
            'account': 'servicelinker-sql-cosmos',
            'database': 'coreDB'
        })


        # create connection
        self.cmd('spring-cloud connection create cosmos-sql --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --account {account} --database {database} --system-identity --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_cosmostable_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-win-group',
            'spring': 'servicelinker-springcloud',
            'app': 'cosmostable',
            'deployment': 'default',
            'account': 'servicelinker-table-cosmos',
            'table': 'MyItem'
        })


        # create connection
        self.cmd('spring-cloud connection create cosmos-table --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --account {account} --table {table} --system-identity --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_eventhub_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'eventhub',
            'deployment': 'default',
            'namespace': 'servicelinkertesteventhub'
        })


        # create connection
        self.cmd('spring-cloud connection create eventhub --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --namespace {namespace} --system-identity --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_postgresflexible_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'postgresflexible',
            'deployment': 'default',
            'server': 'servicelinker-flexiblepostgresql',
            'database': 'postgres',
            'user': 'servicelinker',
        })

        # prepare password
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')

        self.kwargs.update({'password': password})


        # create connection
        self.cmd('spring-cloud connection create postgres-flexible --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_keyvault_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'keyvaultmi',
            'deployment': 'default',
            'vault': 'servicelinker-test-kv'
        })


        # create connection
        self.cmd('spring-cloud connection create keyvault --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --vault {vault} --system-identity --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_mysql_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'mysql',
            'deployment': 'default',
            'server': 'servicelinker-mysql',
            'database': 'mysqlDB',
            'user': 'servicelinker',
        })

        # prepare password
        password = self.cmd('keyvault secret show --vault-name cupertino-kv-test -n TestDbPassword')\
            .get_output_in_json().get('value')
        self.kwargs.update({'password': password})


        # create connection
        self.cmd('spring-cloud connection create mysql --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_mysqlflexible_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
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
        self.kwargs.update({
            'user': user,
            'password': password
        })


        # create connection
        self.cmd('spring-cloud connection create mysql-flexible --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_postgres_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
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
        self.kwargs.update({
            'user': user,
            'password': password
        })


        # create connection
        self.cmd('spring-cloud connection create postgres --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_sql_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
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
        self.kwargs.update({
            'user': user,
            'password': password
        })

        # create connection
        self.cmd('spring-cloud connection create sql --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --server {server} --database {database} --secret name={user} secret={password} --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_storageblob_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'storageblob',
            'deployment': 'default',
            'account': 'servicelinkerteststorage'
        })

        # create connection
        self.cmd('spring-cloud connection create storage-blob --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --account {account} --system-identity --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'systemAssignedIdentity'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_storagequeue_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'storagequeue',
            'deployment': 'default',
            'account': 'servicelinkerteststorage'
        })

        # create connection
        self.cmd('spring-cloud connection create storage-queue --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --account {account} --secret --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_storagefile_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'storagefile',
            'deployment': 'default',
            'account': 'servicelinkerteststorage'
        })

        # create connection
        self.cmd('spring-cloud connection create storage-file --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --account {account} --secret --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')


    # @record_only
    def test_springcloud_storagetable_e2e(self):
        self.kwargs.update({
            'name' : 'testconn3',
            'subscription': get_subscription_id(self.cli_ctx),
            'source_resource_group': 'servicelinker-test-linux-group',
            'target_resource_group': 'servicelinker-test-linux-group',
            'spring': 'servicelinker-springcloud',
            'app': 'storagetable',
            'deployment': 'default',
            'account': 'servicelinkerteststorage'
        })


        # create connection
        self.cmd('spring-cloud connection create storage-table --connection {name} -g {source_resource_group} --service {spring} --app {app} '
                 '--tg {target_resource_group} --account {account} --secret --client-type java')

        # list connection
        connections = self.cmd(
            'spring-cloud connection list -g {source_resource_group} --service {spring} --app {app}',
            checks = [
                # self.check('length(@)', 1),
                self.check('[0].authInfo.authType', 'secret'),
                self.check('[0].clientType', 'java')
            ]
        ).get_output_in_json()
        connection_id = connections[0].get('id')

        # list configuration
        self.cmd('spring-cloud connection list-configuration --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # validate connection
        self.cmd('spring-cloud connection validate --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # show connection
        self.cmd('spring-cloud connection show --connection {name} -g {source_resource_group} --service {spring} --app {app}')

        # delete connection
        self.cmd('spring-cloud connection delete --connection {name} -g {source_resource_group} --service {spring} --app {app} --yes')
