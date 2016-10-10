#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

#pylint: disable=method-hidden
#pylint: disable=line-too-long
#pylint: disable=bad-continuation
import os

from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck,
                                                     NoneCheck)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class KeyVaultMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(KeyVaultMgmtScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli-test-keyvault-mgmt'
        self.keyvault_names = ['cli-keyvault-12345-0',
                               'cli-keyvault-12345-1',
                               'cli-keyvault-12345-2',
                               'cli-keyvault-12345-3']
        self.location = 'westus'

    def test_keyvault_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        kv = self.keyvault_names[0]
        loc = self.location
        # test create keyvault with default access policy set
        keyvault = self.cmd('keyvault create -g {} -n {} -l {}'.format(rg, kv, loc), checks=[
            JMESPathCheck('name', kv),
            JMESPathCheck('location', loc),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('type(properties.accessPolicies)', 'array'),
            JMESPathCheck('length(properties.accessPolicies)', 1),
            JMESPathCheck('properties.sku.name', 'standard')
        ])
        policy_id = keyvault['properties']['accessPolicies'][0]['objectId']
        self.cmd('keyvault show -n {}'.format(kv), checks=[
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
        self.cmd('keyvault update -g {} -n {} --set properties.sku.name=premium'.format(rg, kv), checks=[
            JMESPathCheck('name', kv),
            JMESPathCheck('properties.sku.name', 'premium'),
        ])
        # test policy set/delete
        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --certificate-permissions get list'.format(rg, kv, policy_id),
            checks=JMESPathCheck('length(properties.accessPolicies[0].permissions.certificates)', 2))
        self.cmd('keyvault delete-policy -g {} -n {} --object-id {}'.format(rg, kv, policy_id), checks=[
            JMESPathCheck('type(properties.accessPolicies)', 'array'),
            JMESPathCheck('length(properties.accessPolicies)', 0)
        ])

        # test keyvault delete
        self.cmd('keyvault delete -n {}'.format(kv))
        self.cmd('keyvault list -g {}'.format(rg), checks=NoneCheck())

        # test create keyvault further
        self.cmd('keyvault create -g {} -n {} -l {} --no-self-perms'.format(rg, self.keyvault_names[1], loc), checks=[
            JMESPathCheck('type(properties.accessPolicies)', 'array'),
            JMESPathCheck('length(properties.accessPolicies)', 0)
        ])
        self.cmd('keyvault create -g {} -n {} -l {} --enabled-for-deployment true '\
                 '--enabled-for-disk-encryption true --enabled-for-template-deployment true'.format(rg, self.keyvault_names[2], loc), checks=[
            JMESPathCheck('properties.enabledForDeployment', True),
            JMESPathCheck('properties.enabledForDiskEncryption', True),
            JMESPathCheck('properties.enabledForTemplateDeployment', True)
        ])
        self.cmd('keyvault create -g {} -n {} -l {} --sku premium'.format(rg, self.keyvault_names[3], loc), checks=[
            JMESPathCheck('properties.sku.name', 'premium')
        ])

class KeyVaultKeyScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(KeyVaultKeyScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli-test-keyvault-key'
        self.keyvault_name = 'cli-keyvault-test-key'
        self.location = 'westus'

    def set_up(self):
        super(KeyVaultKeyScenarioTest, self).set_up()
        self.cmd('keyvault create -g {} -n {} -l {}'.format(self.resource_group, self.keyvault_name, self.location))

    def test_keyvault_key(self):
        self.execute()

    def body(self):
        kv = self.keyvault_name
        # create a key
        key = self.cmd('keyvault key create --vault-name {} -n key1 -p software'.format(kv),
            checks=JMESPathCheck('attributes.enabled', True))
        first_kid = key['key']['kid']
        first_version = first_kid.rsplit('/', 1)[1]

        # list keys
        self.cmd('keyvault key list --vault-name {}'.format(kv),
            checks=JMESPathCheck('length(@)', 1))

        # create a new key version
        key = self.cmd('keyvault key create --vault-name {} -n key1 -p software --disabled --ops encrypt decrypt --tags test=foo'.format(kv), checks=[
            JMESPathCheck('attributes.enabled', False),
            JMESPathCheck('length(key.keyOps)', 2),
            JMESPathCheck('tags', {'test':'foo'})
        ])
        second_kid = key['key']['kid']
        # list key versions
        self.cmd('keyvault key list-versions --vault-name {} -n key1'.format(kv),
            checks=JMESPathCheck('length(@)', 2))

        # show key (latest)
        self.cmd('keyvault key show --vault-name {} -n key1'.format(kv),
            checks=JMESPathCheck('key.kid', second_kid))

        # show key (specific version)
        self.cmd('keyvault key show --vault-name {} -n key1 -v {}'.format(kv, first_version),
            checks=JMESPathCheck('key.kid', first_kid))

        # set key attributes
        self.cmd('keyvault key set-attributes --vault-name {} -n key1 --enabled true'.format(kv), checks=[
            JMESPathCheck('key.kid', second_kid),
            JMESPathCheck('attributes.enabled', True)
        ])

        # delete key
        self.cmd('keyvault key delete --vault-name {} -n key1'.format(kv))
        self.cmd('keyvault key list --vault-name {}'.format(kv),
            checks=NoneCheck())

        # PHASE 2 COMMANDS
        # TODO: import PEM key
        # TODO: import BYOK key
        # TODO: backup key
        # TODO: restore key backup

class KeyVaultSecretScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(KeyVaultSecretScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli-test-keyvault-secret'
        self.keyvault_name = 'cli-test-keyvault-secret'
        self.location = 'westus'

    def set_up(self):
        super(KeyVaultSecretScenarioTest, self).set_up()
        self.cmd('keyvault create -g {} -n {} -l {}'.format(self.resource_group, self.keyvault_name, self.location))

    def test_keyvault_secret(self):
        self.execute()

    def body(self):
        kv = self.keyvault_name
        # create a secret
        secret = self.cmd('keyvault secret set --vault-name {} -n secret1 --value ABC123'.format(kv),
            checks=JMESPathCheck('value', 'ABC123'))
        first_kid = secret['id']
        first_version = first_kid.rsplit('/', 1)[1]

        # list secrets
        self.cmd('keyvault secret list --vault-name {}'.format(kv),
            checks=JMESPathCheck('length(@)', 1))

        # create a new secret version
        secret = self.cmd('keyvault secret set --vault-name {} -n secret1 --value DEF456 --tags test=foo --content-type "test type"'.format(kv), checks=[
            JMESPathCheck('value', 'DEF456'),
            JMESPathCheck('tags', {'test':'foo'}),
            JMESPathCheck('contentType', 'test type')
        ])
        second_kid = secret['id']

        # list secret versions
        self.cmd('keyvault secret list-versions --vault-name {} -n secret1'.format(kv),
            checks=JMESPathCheck('length(@)', 2))

        # show secret (latest)
        self.cmd('keyvault secret show --vault-name {} -n secret1'.format(kv),
            checks=JMESPathCheck('id', second_kid))

        # show secret (specific version)
        self.cmd('keyvault secret show --vault-name {} -n secret1 -v {}'.format(kv, first_version),
            checks=JMESPathCheck('id', first_kid))

        # set secret attributes
        self.cmd('keyvault secret set-attributes --vault-name {} -n secret1 --enabled false'.format(kv), checks=[
            JMESPathCheck('id', second_kid),
            JMESPathCheck('attributes.enabled', False)
        ])

        # delete secret
        self.cmd('keyvault secret delete --vault-name {} -n secret1'.format(kv))
        self.cmd('keyvault secret list --vault-name {}'.format(kv),
            checks=NoneCheck())

        # PHASE 2 COMMANDS
        # TODO: download secret
