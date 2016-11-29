# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI ACR TEST DEFINITIONS
#pylint: disable=line-too-long

from azure.cli.core.test_utils.vcr_test_base import (
    ResourceGroupVCRTestBase,
    JMESPathCheck,
    NoneCheck
)

class ACRTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(ACRTest, self).__init__(__file__, test_method)
        self.registry_name_1 = 'acrtestregistry1'
        self.registry_name_2 = 'acrtestregistry2'
        self.resource_group = 'acr_test_resource_group'
        self.storage_account_1 = 'acrteststorage1'
        self.storage_account_2 = 'acrteststorage2'
        self.location = 'southcentralus'

    def test_acr(self):
        self.execute()

    def _test_acr(self, registry_name, storage_account_for_update, storage_account_for_create=None):
        resource_group = self.resource_group
        location = self.location
        # test acr create
        self.cmd('acr check-name -n {}'.format(registry_name), checks=[
            JMESPathCheck('nameAvailable', True)
        ])
        if storage_account_for_create is None:
            self.cmd('acr create -n {} -g {} -l {}'.format(registry_name, resource_group, location), checks=[
                JMESPathCheck('name', registry_name),
                JMESPathCheck('location', location),
                JMESPathCheck('adminUserEnabled', False)
            ])
        else:
            self.cmd('acr create -n {} -g {} -l {} --storage-account-name {}'.format(registry_name, resource_group, location, storage_account_for_create), checks=[
                JMESPathCheck('name', registry_name),
                JMESPathCheck('location', location),
                JMESPathCheck('adminUserEnabled', False),
                JMESPathCheck('storageAccount.name', storage_account_for_create)
            ])
        self.cmd('acr check-name -n {}'.format(registry_name), checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])
        self.cmd('acr list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].name', registry_name),
            JMESPathCheck('[0].location', location),
            JMESPathCheck('[0].adminUserEnabled', False)
        ])
        self.cmd('acr show -n {} -g {}'.format(registry_name, resource_group), checks=[
            JMESPathCheck('name', registry_name),
            JMESPathCheck('location', location),
            JMESPathCheck('adminUserEnabled', False)
        ])
        # enable admin user
        self.cmd('acr update -n {} -g {} --admin-enabled true'.format(registry_name, resource_group), checks=[
            JMESPathCheck('name', registry_name),
            JMESPathCheck('location', location),
            JMESPathCheck('adminUserEnabled', True)
        ])
        # test credential module
        credential = self.cmd('acr credential show -n {} -g {}'.format(registry_name, resource_group))
        username = credential['username']
        password = credential['password']
        assert username and password
        credential = self.cmd('acr credential renew -n {} -g {}'.format(registry_name, resource_group))
        renewed_username = credential['username']
        renewed_password = credential['password']
        assert renewed_username and renewed_password
        assert username == renewed_username
        assert password != renewed_password
        # test repository module
        login_server = self.cmd('acr show -n {} -g {}'.format(registry_name, resource_group))['loginServer']
        assert login_server
        self.cmd('acr repository list -n {}'.format(registry_name), checks=NoneCheck())
        # test acr update
        self.cmd('acr update -n {} -g {} --tags foo=bar cat --admin-enabled false --storage-account-name {}'.format(registry_name, resource_group, storage_account_for_update), checks=[
            JMESPathCheck('name', registry_name),
            JMESPathCheck('location', location),
            JMESPathCheck('tags', {'cat':'', 'foo':'bar'}),
            JMESPathCheck('adminUserEnabled', False),
            JMESPathCheck('storageAccount.name', storage_account_for_update)
        ])
        # test acr delete
        self.cmd('acr delete -n {} -g {}'.format(registry_name, resource_group))

    def body(self):
        self._test_acr(self.registry_name_1, self.storage_account_1, self.storage_account_2)
        self._test_acr(self.registry_name_2, self.storage_account_1)

    def set_up(self):
        super(ACRTest, self).set_up()
        self.cmd('storage account create -n {} -g {} -l {} --sku Standard_LRS '.format(self.storage_account_1, self.resource_group, self.location), checks=[
            JMESPathCheck('name', self.storage_account_1),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('location', self.location),
            JMESPathCheck('sku.name', 'Standard_LRS')
        ])
        self.cmd('storage account create -n {} -g {} -l {} --sku Standard_LRS '.format(self.storage_account_2, self.resource_group, self.location), checks=[
            JMESPathCheck('name', self.storage_account_2),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('location', self.location),
            JMESPathCheck('sku.name', 'Standard_LRS')
        ])

    def tear_down(self):
        super(ACRTest, self).tear_down()
