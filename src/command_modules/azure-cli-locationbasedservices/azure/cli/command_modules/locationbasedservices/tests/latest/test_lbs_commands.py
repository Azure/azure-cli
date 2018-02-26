# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.mgmt.locationbasedservices.models.client_enums import KeyType


class LocationBasedServicesScenarioTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_create_locationbasedservices_account(self, resource_group):
        self.kwargs.update({
            'name': self.create_random_name(prefix='cli-', length=20),
            'name1': self.create_random_name(prefix='cli-', length=20),
            'name2': self.create_random_name(prefix='cli-', length=20),
            'sku': 'S0',
            'tags': 'a=b',
            'key_type_primary': KeyType.primary.value,
            'key_type_secondary': KeyType.secondary.value
        })

        # Test 'az locationbasedservices account create'
        # Test to create an LocationBasedServices account
        account = self.cmd('az locationbasedservices account create -n {name} -g {rg} --sku {sku} ' +
                           '--agree-to-the-preview-terms',
                           checks=[
                               self.check('name', '{name}'),
                               self.check('resourceGroup', '{rg}'),
                               self.check('sku.name', '{sku}')
                           ]).get_output_in_json()

        # Call create again, expect to get the same account
        account_duplicated = self.cmd(
            'az locationbasedservices account create -n {name} -g {rg} --sku {sku} ' +
            '--agree-to-the-preview-terms').get_output_in_json()
        self.assertEqual(account, account_duplicated)

        # Test 'az locationbasedservices account show'
        # Test to get information on LocationBasedServices account
        self.cmd('az locationbasedservices account show -n {name} -g {rg}', checks=[
            self.check('id', account['id']),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('sku.name', '{sku}')
        ])

        # Test 'az locationbasedservices account list'
        # Test to list all LocationBasedServices accounts under a resource group
        self.cmd('az locationbasedservices account list -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('type(@)', 'array'),
            self.check('[0].id', account['id']),
            self.check('[0].name', '{name}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].sku.name', '{sku}'),
            self.check('[0].tags', None)
        ])

        # Create two new accounts
        self.cmd('az locationbasedservices account create -n {name1} -g {rg} --sku {sku} ' +
                 '--agree-to-the-preview-terms')
        self.cmd('az locationbasedservices account create -n {name2} -g {rg} --sku {sku} ' +
                 '--agree-to-the-preview-terms')
        # Check that list command now shows three accounts.
        self.cmd('az locationbasedservices account list -g {rg}', checks=[
            self.check('length(@)', 3),
            self.check('type(@)', 'array'),
            self.check("length([?name == '{name}'])", 1),
            self.check("length([?name == '{name1}'])", 1),
            self.check("length([?name == '{name2}'])", 1),
            self.check("length([?resourceGroup == '{rg}'])", 3)
        ])

        # Test 'az locationbasedservices account key list'
        # Test to list keys for an LocationBasedServices account
        account_key_list = self.cmd('az locationbasedservices account key list -n {name} -g {rg}', checks=[
            self.check('id', account['id']),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        # Retrieve primary and secondary keys
        primary_key_old = account_key_list['primaryKey']
        secondary_key_old = account_key_list['secondaryKey']
        self.assertTrue(re.match('^[a-zA-Z0-9_-]+$', primary_key_old))
        self.assertTrue(re.match('^[a-zA-Z0-9_-]+$', secondary_key_old))

        # Test 'az locationbasedservices account key regenerate'
        # Test to change primary and secondary keys for an LocationBasedServices account
        key_regenerated = self.cmd(
            'az locationbasedservices account key regenerate -n {name} -g {rg} -t {key_type_primary}', checks=[
                self.check('id', account['id']),
                self.check('resourceGroup', '{rg}')
            ]).get_output_in_json()

        # Only primary key was regenerated. Secondary key should remain same.
        self.assertNotEqual(primary_key_old, key_regenerated['primaryKey'])
        self.assertEqual(secondary_key_old, key_regenerated['secondaryKey'])

        # Save the new primary key, and regenerate the secondary key.
        primary_key_old = key_regenerated['primaryKey']
        key_regenerated = self.cmd(
            'az locationbasedservices account key regenerate -n {name} -g {rg} -t {key_type_secondary}') \
            .get_output_in_json()
        self.assertEqual(primary_key_old, key_regenerated['primaryKey'])
        self.assertNotEqual(secondary_key_old, key_regenerated['secondaryKey'])

        # Test 'az locationbasedservices account delete'
        # Test to remove an LocationBasedServices account
        self.cmd('az locationbasedservices account delete -n {name} -g {rg}', checks=self.is_empty())
        self.cmd('az locationbasedservices account show -n {name} -g {rg}', checks=self.is_empty())
        self.cmd('az locationbasedservices account list -g {rg}', checks=[
            self.check('length(@)', 2),
            self.check("length([?name == '{name}'])", 0)
        ])

        # Remove the rest of LocationBasedServices accounts
        exit_code = self.cmd('az locationbasedservices account delete -n {name1} -g {rg}').exit_code
        self.assertEqual(exit_code, 0)
        self.cmd('az locationbasedservices account delete -n {name2} -g {rg}')
        self.cmd('az locationbasedservices account list -g {rg}', checks=self.is_empty())
