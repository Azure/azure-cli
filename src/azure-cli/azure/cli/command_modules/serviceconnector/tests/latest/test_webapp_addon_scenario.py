# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from unittest.signals import installHandler
from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.testsdk.scenario_tests import (
    AllowLargeResponse,
    RecordingProcessor
)
from azure.cli.testsdk.scenario_tests.utilities import is_text_payload
from azure.cli.testsdk import (
    ScenarioTest, 
    live_only
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


class WebAppAddonScenarioTest(ScenarioTest):

    def __init__(self, method_name):
        super(WebAppAddonScenarioTest, self).__init__(
            method_name,
            recording_processors=[CredentialReplacer()]
        )

    @AllowLargeResponse()
    @live_only()
    def test_webapp_postgres_addon(self):
        self.kwargs.update({
            'rg': 'clitest',
            'loc': 'eastus',
            'plan': 'testplan',
            'app': 'servicelinker-clitest-app'
        })

        # prepare webapp
        self.cmd('group create -n {rg} -l {loc}')
        self.cmd('appservice plan create -g {rg} -n {plan}')
        webapp = self.cmd('webapp create -g {rg} -p {plan} -n {app}').get_output_in_json()
        source_id = webapp.get('id')

        # servicelinker provision experience
        connection_name = 'testconn_postgres'
        connection = self.cmd('webapp connection create postgres --source-id {} '
                              '--connection {} --new'.format(source_id, connection_name)).get_output_in_json()
        target_id = connection.get('targetId')
        connection_id = connection.get('id')

        # validate the created postgres
        server_name = target_id.split('/')[-3]
        db_name = target_id.split('/')[-1]
        self.cmd('postgres db show -g {} -s {} -n {}'.format(self.kwargs.get('rg'), server_name, db_name))
        self.cmd('webapp connection show --id {}'.format(connection_id))


    @AllowLargeResponse()
    @live_only()
    def test_webapp_keyvault_addon(self):
        self.kwargs.update({
            'rg': 'clitest',
            'loc': 'eastus',
            'plan': 'testplan',
            'app': 'servicelinker-clitest-app'
        })

        # prepare webapp
        self.cmd('group create -n {rg} -l {loc}')
        self.cmd('appservice plan create -g {rg} -n {plan}')
        webapp = self.cmd('webapp create -g {rg} -p {plan} -n {app}').get_output_in_json()
        source_id = webapp.get('id')

        # servicelinker provision experience
        connection_name = 'testconn_keyvault'
        connection = self.cmd('webapp connection create keyvault --source-id {} '
                              '--connection {} --new'.format(source_id, connection_name)).get_output_in_json()
        target_id = connection.get('targetId')
        connection_id = connection.get('id')

        # validate the created postgres
        vault_name = target_id.split('/')[-1]
        self.cmd('keyvault show --connection {}'.format(vault_name))
        self.cmd('webapp connection show --id {}'.format(connection_id))


    @AllowLargeResponse()
    @live_only()
    def test_webapp_storageblob_addon(self):
        self.kwargs.update({
            'rg': 'clitest',
            'loc': 'eastus',
            'plan': 'testplan',
            'app': 'servicelinker-clitest-app'
        })

        # prepare webapp
        self.cmd('group create -n {rg} -l {loc}')
        self.cmd('appservice plan create -g {rg} -n {plan}')
        webapp = self.cmd('webapp create -g {rg} -p {plan} -n {app}').get_output_in_json()
        source_id = webapp.get('id')

        # servicelinker provision experience
        connection_name = 'testconn_storageblob'
        connection = self.cmd('webapp connection create storage-blob --source-id {} '
                              '--connection {} --new'.format(source_id, connection_name)).get_output_in_json()
        target_id = connection.get('targetId')
        connection_id = connection.get('id')

        # validate the created postgres
        account_name = target_id.split('/')[-3]
        self.cmd('storage account show --connection {}'.format(account_name))
        self.cmd('webapp connection show --id {}'.format(connection_id))
