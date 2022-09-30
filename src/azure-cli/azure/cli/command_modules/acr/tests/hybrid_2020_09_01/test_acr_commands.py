# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, KeyVaultPreparer, record_only
from azure.cli.command_modules.acr.custom import DEF_DIAG_SETTINGS_NAME_TEMPLATE


class AcrCommandsTests(ScenarioTest):

    def _core_registry_scenario(self, registry_name, resource_group, location):
        self.cmd('acr check-name -n {}'.format(registry_name),
                 checks=[self.check('nameAvailable', False),
                         self.check('reason', 'AlreadyExists')])
        self.cmd('acr list -g {}'.format(resource_group),
                 checks=[self.check('[0].name', registry_name),
                         self.check('[0].location', location),
                         self.check('[0].adminUserEnabled', False)])
        registry = self.cmd('acr show -n {} -g {}'.format(registry_name, resource_group),
                            checks=[self.check('name', registry_name),
                                    self.check('location', location),
                                    self.check('adminUserEnabled', False)]).get_output_in_json()

        if registry['sku']['name'] == 'Premium':
            self.cmd('acr show-usage -n {} -g {}'.format(registry_name, resource_group))

        # enable admin user
        self.cmd('acr update -n {} -g {} --tags foo=bar cat --admin-enabled true'.format(registry_name, resource_group),
                 checks=[self.check('name', registry_name),
                         self.check('location', location),
                         self.check('tags', {'cat': '', 'foo': 'bar'}),
                         self.check('adminUserEnabled', True),
                         self.check('provisioningState', 'Succeeded')])

        # test retention
        self.cmd('acr config retention update -r {} --status enabled --days 30 --type UntaggedManifests'.format(registry_name),
                 checks=[self.check('status', "enabled"),
                         self.check('days', 30)])

        self.cmd('acr config retention show -r {}'.format(registry_name),
                 checks=[self.check('status', "enabled"),
                         self.check('days', 30)])

        # test content-trust
        self.cmd('acr config content-trust update -n {} --status enabled'.format(registry_name),
                 checks=[self.check('status', "enabled")])

        self.cmd('acr config content-trust show -n {}'.format(registry_name),
                 checks=[self.check('status', "enabled")])

        # test credential module
        credential = self.cmd(
            'acr credential show -n {} -g {}'.format(registry_name, resource_group)).get_output_in_json()
        username = credential['username']
        password = credential['passwords'][0]['value']
        password2 = credential['passwords'][1]['value']
        assert username and password and password2

        # renew password
        credential = self.cmd('acr credential renew -n {} -g {} --password-name {}'.format(
            registry_name, resource_group, 'password')).get_output_in_json()
        renewed_username = credential['username']
        renewed_password = credential['passwords'][0]['value']
        renewed_password2 = credential['passwords'][1]['value']
        assert renewed_username and renewed_password and renewed_password2
        assert username == renewed_username
        assert password != renewed_password
        assert password2 == renewed_password2

        # renew password2
        credential = self.cmd('acr credential renew -n {} -g {} --password-name {}'.format(
            registry_name, resource_group, 'password2')).get_output_in_json()
        renewed_username = credential['username']
        renewed_password = credential['passwords'][0]['value']
        renewed_password2 = credential['passwords'][1]['value']
        assert renewed_username and renewed_password and renewed_password2
        assert username == renewed_username
        assert password != renewed_password
        assert password2 != renewed_password2

        # test acr delete
        self.cmd('acr delete -n {} -g {} -y'.format(registry_name, resource_group))

    def test_check_name_availability(self):
        # the chance of this randomly generated name has a duplication is rare
        name = self.create_random_name('clireg', 20)
        self.kwargs.update({
            'name': name
        })

        self.cmd('acr check-name -n {name}', checks=[
            self.check('nameAvailable', True)
        ])

    @ResourceGroupPreparer()
    def test_acr_create_with_managed_registry(self, resource_group, resource_group_location):
        registry_name = self.create_random_name('clireg', 20)

        self.kwargs.update({
            'registry_name': registry_name,
            'rg_loc': resource_group_location,
            'sku': 'Premium'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Premium'),
                         self.check('sku.tier', 'Premium'),
                         self.check('provisioningState', 'Succeeded')])

        self._core_registry_scenario(registry_name, resource_group, resource_group_location)

    @ResourceGroupPreparer()
    def test_acr_create_webhook(self, resource_group, resource_group_location):
        registry_name = self.create_random_name('clireg', 20)
        webhook_name = 'cliregwebhook'

        self.kwargs.update({
            'registry_name': registry_name,
            'webhook_name': webhook_name,
            'rg_loc': resource_group_location,
            'headers': 'key=value',
            'webhook_scope': 'hello-world',
            'uri': 'http://www.microsoft.com',
            'actions': 'push',
            'sku': 'Standard'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('acr webhook create -n {webhook_name} -r {registry_name} --uri {uri} --actions {actions}',
                 checks=[self.check('name', '{webhook_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('status', 'enabled'),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('acr webhook list -r {registry_name}',
                 checks=[self.check('[0].name', '{webhook_name}'),
                         self.check('[0].status', 'enabled'),
                         self.check('[0].provisioningState', 'Succeeded')])
        self.cmd('acr webhook show -n {webhook_name} -r {registry_name}',
                 checks=[self.check('name', '{webhook_name}'),
                         self.check('status', 'enabled'),
                         self.check('provisioningState', 'Succeeded')])

        # update webhook
        self.cmd('acr webhook update -n {webhook_name} -r {registry_name} --headers {headers} --scope {webhook_scope}',
                 checks=[self.check('name', '{webhook_name}'),
                         self.check('status', 'enabled'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('scope', '{webhook_scope}')])

        # get webhook config
        self.cmd('acr webhook get-config -n {webhook_name} -r {registry_name}',
                 checks=[self.check('serviceUri', '{uri}'),
                         self.check('customHeaders', {'key': 'value'})])
        # ping
        self.cmd('acr webhook ping -n {webhook_name} -r {registry_name}', checks=[self.exists('id')])
        # list webhook events
        self.cmd('acr webhook list-events -n {webhook_name} -r {registry_name}')

        # get registry usage
        self.cmd('acr show-usage -n {registry_name} -g {rg}',
                 checks=[self.check('value[?name==`Size`]|[0].currentValue', 0),
                         self.greater_than('value[?name==`Size`]|[0].limit', 0),
                         self.check('value[?name==`Webhooks`]|[0].currentValue', 1),
                         self.greater_than('value[?name==`Webhooks`]|[0].limit', 0)])

        # test webhook delete
        self.cmd('acr webhook delete -n {webhook_name} -r {registry_name}')
        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg} -y')
