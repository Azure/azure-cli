# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import uuid


class AuthSettingTests(ScenarioTest):

    @ResourceGroupPreparer(random_name_length=20)
    def test_auth_setting(self, resource_group):
        self.kwargs.update({
            'botname': self.create_random_name(prefix='cli', length=10),
            'endpoint': 'https://www.google.com/api/messages',
            'app_id': str(uuid.uuid4()),
            'setting_name': self.create_random_name(prefix='auth', length=10),
            'clientid': 'clientid',
            'secret': 'secret',
            'password': str(uuid.uuid4())
        })

        self.cmd('az bot create -g {rg} -n {botname} -e {endpoint} --app-type MultiTenant --appid {app_id}', checks=[
            self.check('name', '{botname}'),
            self.check('resourceGroup', '{rg}'),
            self.check('location', 'global')
        ])

        self.cmd('az bot authsetting create -g {rg} -n {botname} --client-id {clientid} --client-secret {secret} --provider-scope-string "scope1 scope2" --service google -c myconnname', checks=[
            self.check('properties.clientId', '{clientid}')
        ])

        self.cmd('az bot authsetting show -c myconnname -g {rg} -n {botname}', checks=[
            self.check('properties.clientId', '{clientid}')
        ])

        self.cmd('az bot authsetting list -n {botname} -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].properties.name', 'myconnname')
        ])

        self.cmd('az bot authsetting delete -g {rg} -n {botname} -c myconnname')

    def test_service_providers(self):
        self.kwargs.update({
            'service_provider': 'google'
        })

        self.cmd('az bot authsetting list-providers', checks=[
            self.greater_than('length(@)', 0)
        ])

        self.cmd('az bot authsetting list-providers --provider-name {service_provider}', checks=[
            self.check('length(@)', 1),
            self.check('properties.serviceProviderName', '{service_provider}')
        ])
