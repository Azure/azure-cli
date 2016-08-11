#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

#pylint: disable=method-hidden
#pylint: disable=line-too-long
#pylint: disable=bad-continuation
import os

from azure.cli.utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck,
                                           NoneCheck)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class KeyVaultMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(KeyVaultMgmtScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'keyvault1rg'
        self.keyvault_names = ['cli-keyvault-12345-0',
                               'cli-keyvault-12345-1',
                               'cli-keyvault-12345-2',
                               'cli-keyvault-12345-3']
        self.location = 'westus'
        self.mock_object_id = '00000000-0000-0000-0000-000000000000'

    def test_key_vault_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        kv = self.keyvault_names[0]
        loc = self.location
        # test create keyvault with default access policy set
        self.cmd('keyvault create -g {} -n {} -l {}'.format(rg, kv, loc), checks=[
            JMESPathCheck('name', kv),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('type(properties.accessPolicies)', 'array'),
            JMESPathCheck('length(properties.accessPolicies)', 1),
        ])
        self.cmd('keyvault show -g {} -n {}'.format(rg, kv), checks=[
            JMESPathCheck('name', kv),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('type(properties.accessPolicies)', 'array'),
            JMESPathCheck('length(properties.accessPolicies)', 1),
        ])
        self.cmd('keyvault list -g {}'.format(rg), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', kv),
            JMESPathCheck('[0].location', loc),
            JMESPathCheck('[0].resourceGroup', rg),
        ])
        # test updating keyvault sku name
        self.cmd('keyvault show -g {} -n {}'.format(rg, kv), checks=[
            JMESPathCheck('name', kv),
            JMESPathCheck('properties.sku.name', 'standard'),
        ])
        self.cmd('keyvault update -g {} -n {} --set properties.sku.name=premium'.format(rg, kv),
        checks=[
            JMESPathCheck('name', kv),
            JMESPathCheck('properties.sku.name', 'premium'),
        ])
        # test policy set/delete
        # the object id is mocked so we expect the service raise an error
        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --perms-to-secrets get list'.format(rg, kv, self.mock_object_id),
        allowed_exceptions="An invalid value was provided for 'accessPolicies'.")
        self.cmd('keyvault delete-policy -g {} -n {} --object-id {}'.format(rg, kv, self.mock_object_id),
        allowed_exceptions="No matching policies found")
        # test keyvault delete
        self.cmd('keyvault delete -g {} -n {}'.format(rg, kv))
        self.cmd('keyvault list -g {}'.format(rg), checks=NoneCheck())

        # test create keyvault further
        self.cmd('keyvault create -g {} -n {} -l {} --no-self-perms'.format(rg, self.keyvault_names[1], loc), checks=[
            JMESPathCheck('type(properties.accessPolicies)', 'array'),
            JMESPathCheck('length(properties.accessPolicies)', 0),
        ])
        self.cmd('keyvault create -g {} -n {} -l {} --enabled-for-deployment true '\
                 '--enabled-for-disk-encryption true --enabled-for-template-deployment true'.format(rg, self.keyvault_names[2], loc), checks=[
            JMESPathCheck('properties.enabledForDeployment', True),
            JMESPathCheck('properties.enabledForDiskEncryption', True),
            JMESPathCheck('properties.enabledForTemplateDeployment', True),
        ])
        self.cmd('keyvault create -g {} -n {} -l {} --sku premium'.format(rg, self.keyvault_names[3], loc), checks=[
            JMESPathCheck('properties.sku.name', 'premium'),
        ])



