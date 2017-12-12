# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, JMESPathCheckExists, JMESPathCheckGreaterThan,
                               StorageAccountPreparer, ResourceGroupPreparer)


class AcrCommandsTests(ScenarioTest):
    def test_check_name_availability(self):
        # the chance of this randomly generated name has a duplication is rare
        name = self.create_random_name('clireg', 20)
        self.cmd('acr check-name -n {}'.format(name), checks=JMESPathCheck('nameAvailable', True))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_acr_create_with_new_storage(self, resource_group, resource_group_location,
                                         storage_account_for_update):
        registry_name = self.create_random_name('clireg', 20)

        self.cmd('acr create -n {} -g {} -l {} --sku {} --deployment-name {}'.format(
            registry_name,
            resource_group,
            resource_group_location,
            'Classic',
            'Microsoft.ContainerRegistry'),
            checks=[JMESPathCheck('name', registry_name),
                    JMESPathCheck('location', resource_group_location),
                    JMESPathCheck('adminUserEnabled', False),
                    JMESPathCheck('sku.name', 'Classic'),
                    JMESPathCheck('sku.tier', 'Classic'),
                    JMESPathCheck('provisioningState', 'Succeeded')])
        self._core_registry_scenario(registry_name, resource_group, resource_group_location,
                                     storage_account_for_update)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_acr_create_with_existing_storage(self, resource_group, resource_group_location,
                                              storage_account_for_update,
                                              storage_account_for_create):
        registry_name = self.create_random_name('clireg', 20)

        self.cmd('acr create -n {} -g {} -l {} --sku {} --storage-account-name {} --deployment-name {}'.format(
            registry_name,
            resource_group,
            resource_group_location,
            'Classic',
            storage_account_for_create,
            'Microsoft.ContainerRegistry'),
            checks=[JMESPathCheck('name', registry_name),
                    JMESPathCheck('location', resource_group_location),
                    JMESPathCheck('adminUserEnabled', False),
                    JMESPathCheck('sku.name', 'Classic'),
                    JMESPathCheck('sku.tier', 'Classic'),
                    JMESPathCheck('provisioningState', 'Succeeded')])

        self._core_registry_scenario(registry_name, resource_group, resource_group_location,
                                     storage_account_for_update)

    @ResourceGroupPreparer()
    def test_acr_create_with_managed_registry(self, resource_group, resource_group_location):
        registry_name = self.create_random_name('clireg', 20)

        self.cmd('acr create -n {} -g {} -l {} --sku {} --deployment-name {}'.format(
            registry_name,
            resource_group,
            resource_group_location,
            'Standard',
            'Microsoft.ContainerRegistry'),
            checks=[JMESPathCheck('name', registry_name),
                    JMESPathCheck('location', resource_group_location),
                    JMESPathCheck('adminUserEnabled', False),
                    JMESPathCheck('sku.name', 'Standard'),
                    JMESPathCheck('sku.tier', 'Standard'),
                    JMESPathCheck('provisioningState', 'Succeeded')])

        self._core_registry_scenario(registry_name, resource_group, resource_group_location)

    @ResourceGroupPreparer()
    def test_acr_create_webhook(self, resource_group, resource_group_location):
        registry_name = self.create_random_name('clireg', 20)
        webhook_name = 'cliregwebhook'

        self.cmd('acr create -n {} -g {} -l {} --sku {} --deployment-name {}'.format(
            registry_name,
            resource_group,
            resource_group_location,
            'Standard',
            'Microsoft.ContainerRegistry'),
            checks=[
                JMESPathCheck('name', registry_name),
                JMESPathCheck('location', resource_group_location),
                JMESPathCheck('adminUserEnabled', False),
                JMESPathCheck('sku.name', 'Standard'),
                JMESPathCheck('sku.tier', 'Standard'),
                JMESPathCheck('provisioningState', 'Succeeded')])

        self.cmd('acr webhook create -n {} -r {} --uri {} --actions {}'.format(
            webhook_name,
            registry_name,
            'http://www.microsoft.com',
            'push'),
            checks=[JMESPathCheck('name', webhook_name),
                    JMESPathCheck('location', resource_group_location),
                    JMESPathCheck('status', 'enabled'),
                    JMESPathCheck('provisioningState', 'Succeeded')])

        self.cmd('acr webhook list -r {}'.format(registry_name),
                 checks=[JMESPathCheck('[0].name', webhook_name),
                         JMESPathCheck('[0].status', 'enabled'),
                         JMESPathCheck('[0].provisioningState', 'Succeeded')])
        self.cmd('acr webhook show -n {} -r {}'.format(webhook_name, registry_name),
                 checks=[JMESPathCheck('name', webhook_name),
                         JMESPathCheck('status', 'enabled'),
                         JMESPathCheck('provisioningState', 'Succeeded')])

        # update webhook
        self.cmd('acr webhook update -n {} -r {} --headers {} --scope {}'.format(
            webhook_name, registry_name, 'key=value', 'hello-world'),
            checks=[JMESPathCheck('name', webhook_name),
                    JMESPathCheck('status', 'enabled'),
                    JMESPathCheck('provisioningState', 'Succeeded'),
                    JMESPathCheck('scope', 'hello-world')])

        # get webhook config
        self.cmd('acr webhook get-config -n {} -r {}'.format(webhook_name, registry_name),
                 checks=[JMESPathCheck('serviceUri', 'http://www.microsoft.com'),
                         JMESPathCheck('customHeaders', {'key': 'value'})])
        # ping
        self.cmd('acr webhook ping -n {} -r {}'.format(webhook_name, registry_name),
                 checks=[JMESPathCheckExists('id')])
        # list webhook events
        self.cmd('acr webhook list-events -n {} -r {}'.format(webhook_name, registry_name))

        # get registry usage
        self.cmd('acr show-usage -n {} -g {}'.format(registry_name, resource_group),
                 checks=[JMESPathCheck('value[?name==`Size`]|[0].currentValue', 0),
                         JMESPathCheckGreaterThan('value[?name==`Size`]|[0].limit', 0),
                         JMESPathCheck('value[?name==`Webhooks`]|[0].currentValue', 1),
                         JMESPathCheckGreaterThan('value[?name==`Webhooks`]|[0].limit', 0)])

        # test webhook delete
        self.cmd('acr webhook delete -n {} -r {}'.format(webhook_name, registry_name))
        # test acr delete
        self.cmd('acr delete -n {} -g {}'.format(registry_name, resource_group))

    @ResourceGroupPreparer()
    def test_acr_create_replication(self, resource_group, resource_group_location):
        registry_name = self.create_random_name('clireg', 20)
        # replication location should be different from registry location
        replication_location = 'southcentralus'
        replication_name = replication_location

        self.cmd('acr create -n {} -g {} -l {} --sku {} --deployment-name {}'.format(
            registry_name,
            resource_group,
            resource_group_location,
            'Premium',
            'Microsoft.ContainerRegistry'),
            checks=[JMESPathCheck('name', registry_name),
                    JMESPathCheck('location', resource_group_location),
                    JMESPathCheck('adminUserEnabled', False),
                    JMESPathCheck('sku.name', 'Premium'),
                    JMESPathCheck('sku.tier', 'Premium'),
                    JMESPathCheck('provisioningState', 'Succeeded')])

        self.cmd('acr replication create -n {} -r {} -l {}'.format(
            replication_name,
            registry_name,
            replication_location),
            checks=[
                JMESPathCheck('name', replication_name),
                JMESPathCheck('location', replication_location),
                JMESPathCheck('provisioningState', 'Succeeded')])

        self.cmd('acr replication list -r {}'.format(registry_name),
                 checks=[JMESPathCheck('[0].provisioningState', 'Succeeded'),
                         JMESPathCheck('[1].provisioningState', 'Succeeded')])
        self.cmd('acr replication show -n {} -r {}'.format(replication_name, registry_name),
                 checks=[JMESPathCheck('name', replication_name),
                         JMESPathCheck('provisioningState', 'Succeeded')])

        # update replication
        self.cmd('acr replication update -n {} -r {} --tags {}'.format(
            replication_name, registry_name, 'key=value'), checks=[JMESPathCheck('name', replication_name),
                                                                   JMESPathCheck('provisioningState', 'Succeeded'),
                                                                   JMESPathCheck('tags', {'key': 'value'})])

        # test replication delete
        self.cmd('acr replication delete -n {} -r {}'.format(replication_name, registry_name))
        # test acr delete
        self.cmd('acr delete -n {} -g {}'.format(registry_name, resource_group))

    def _core_registry_scenario(self, registry_name, resource_group, location,
                                storage_account_for_update=None):
        self.cmd('acr check-name -n {}'.format(registry_name),
                 checks=[JMESPathCheck('nameAvailable', False),
                         JMESPathCheck('reason', 'AlreadyExists')])
        self.cmd('acr list -g {}'.format(resource_group),
                 checks=[JMESPathCheck('[0].name', registry_name),
                         JMESPathCheck('[0].location', location),
                         JMESPathCheck('[0].adminUserEnabled', False)])
        self.cmd('acr show -n {} -g {}'.format(registry_name, resource_group),
                 checks=[JMESPathCheck('name', registry_name),
                         JMESPathCheck('location', location),
                         JMESPathCheck('adminUserEnabled', False)])

        # enable admin user
        self.cmd('acr update -n {} -g {} --tags foo=bar cat --admin-enabled true'.format(registry_name, resource_group),
                 checks=[JMESPathCheck('name', registry_name),
                         JMESPathCheck('location', location),
                         JMESPathCheck('tags', {'cat': '', 'foo': 'bar'}),
                         JMESPathCheck('adminUserEnabled', True),
                         JMESPathCheck('provisioningState', 'Succeeded')])

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

        # test acr storage account update
        if storage_account_for_update is not None:
            self.cmd('acr update -n {} -g {} --storage-account-name {}'.format(
                registry_name, resource_group, storage_account_for_update),
                checks=[JMESPathCheck('name', registry_name),
                        JMESPathCheck('location', location)])

        # test acr delete
        self.cmd('acr delete -n {} -g {}'.format(registry_name, resource_group))
