# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, JMESPathCheckExists, NoneCheck,
                               StorageAccountPreparer, ResourceGroupPreparer)


class AcrCommandsTests(ScenarioTest):
    def test_check_name_availability(self):
        # the chance of this randomly generated name has a duplication is rare
        name = self.create_random_name('clireg', 50)
        self.cmd('acr check-name -n {}'.format(name), checks=JMESPathCheck('nameAvailable', True))

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_acr_create_with_new_storage(self, resource_group, resource_group_location,
                                         storage_account_for_update):
        self._core_create_scenario(resource_group, resource_group_location,
                                   storage_account_for_update)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_for_create')
    @StorageAccountPreparer(parameter_name='storage_account_for_update')
    def test_acr_create_with_existing_storage(self, resource_group, resource_group_location,
                                              storage_account_for_update,
                                              storage_account_for_create):
        self._core_create_scenario(resource_group, resource_group_location,
                                   storage_account_for_update,
                                   storage_account_for_create)

    def _core_create_scenario(self, resource_group, location, storage_account_for_update,
                              storage_account_for_create=None):
        registry_name = self.create_random_name('clireg', 50)

        if storage_account_for_create is None:
            self.cmd('acr create -n {} -g {} -l {} --sku {} --deployment-name {}'.format(
                     registry_name,
                     resource_group,
                     location,
                     'Basic',
                     'Microsoft.ContainerRegistry'),
                     checks=[
                         JMESPathCheck('name', registry_name),
                         JMESPathCheck('location', location),
                         JMESPathCheck('adminUserEnabled', False),
                         JMESPathCheck('sku.name', 'Basic'),
                         JMESPathCheck('sku.tier', 'Basic'),
                         JMESPathCheck('provisioningState', 'Succeeded')])
        else:
            self.cmd('acr create -n {} -g {} -l {} --sku {} '
                     '--storage-account-name {} --deployment-name {}'.format(
                         registry_name,
                         resource_group,
                         location,
                         'Basic',
                         storage_account_for_create,
                         'Microsoft.ContainerRegistry'),
                     checks=[
                         JMESPathCheck('name', registry_name),
                         JMESPathCheck('location', location),
                         JMESPathCheck('adminUserEnabled', False),
                         JMESPathCheck('sku.name', 'Basic'),
                         JMESPathCheck('sku.tier', 'Basic'),
                         JMESPathCheck('provisioningState', 'Succeeded'),
                         JMESPathCheck('storageAccount.name', storage_account_for_create)])

        self.cmd('acr check-name -n {}'.format(registry_name), checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])
        self.cmd('acr list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].name', registry_name),
            JMESPathCheck('[0].location', location),
            JMESPathCheck('[0].adminUserEnabled', False)
        ])
        self.cmd('acr show -n {} -g {}'.format(
            registry_name, resource_group), checks=[
                JMESPathCheck('name', registry_name),
                JMESPathCheck('location', location),
                JMESPathCheck('adminUserEnabled', False)])
        # enable admin user
        self.cmd('acr update -n {} -g {} --admin-enabled true'.format(
            registry_name, resource_group), checks=[
                JMESPathCheck('name', registry_name),
                JMESPathCheck('location', location),
                JMESPathCheck('adminUserEnabled', True)])
        # test credential module
        credential = self.cmd('acr credential show -n {} -g {}'.format(
            registry_name, resource_group)).get_output_in_json()
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
        # test repository module
        self.cmd('acr show -n {} -g {}'.format(registry_name, resource_group),
                 checks=JMESPathCheckExists('loginServer'))
        self.cmd('acr repository list -n {}'.format(registry_name), checks=NoneCheck())
        # test acr update
        self.cmd('acr update -n {} -g {} --tags foo=bar cat --admin-enabled false '
                 '--storage-account-name {}'.format(
                     registry_name, resource_group, storage_account_for_update),
                 checks=[
                     JMESPathCheck('name', registry_name),
                     JMESPathCheck('location', location),
                     JMESPathCheck('tags', {'cat': '', 'foo': 'bar'}),
                     JMESPathCheck('adminUserEnabled', False),
                     JMESPathCheck('sku.name', 'Basic'),
                     JMESPathCheck('sku.tier', 'Basic'),
                     JMESPathCheck('provisioningState', 'Succeeded'),
                     JMESPathCheck('storageAccount.name', storage_account_for_update)
                 ])
        # test acr delete
        self.cmd('acr delete -n {} -g {}'.format(registry_name, resource_group))
