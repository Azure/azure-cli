# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import (
    AllowLargeResponse
)
from azure.cli.testsdk import (
    ScenarioTest, 
    live_only
)
from ._test_utils import CredentialReplacer


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
        target_id = connection.get('targetService', dict()).get('id')
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
        target_id = connection.get('targetService', dict()).get('id')
        connection_id = connection.get('id')

        # validate the created postgres
        vault_name = target_id.split('/')[-1]
        self.cmd('keyvault show --name {}'.format(vault_name))
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
        target_id = connection.get('targetService', dict()).get('id')
        connection_id = connection.get('id')

        # validate the created postgres
        account_name = target_id.split('/')[-3]
        self.cmd('storage account show --name {}'.format(account_name))
        self.cmd('webapp connection show --id {}'.format(connection_id))
