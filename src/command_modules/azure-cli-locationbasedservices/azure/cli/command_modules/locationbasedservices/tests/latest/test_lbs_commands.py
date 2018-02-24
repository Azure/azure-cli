# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.mgmt.locationbasedservices.models.client_enums import KeyType


class LocationBasedServicesScenarioTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_create_lbs_account(self, resource_group):
        self.kwargs.update({
            'name': self.create_random_name(prefix='cli-lbs', length=20),
            'name1': self.create_random_name(prefix='cli-lbs', length=20),
            'name2': self.create_random_name(prefix='cli-lbs', length=20),
            'sku': 'S0',
            'loc': 'global',
            'key_type_primary': KeyType.primary.value,
            'key_type_secondary': KeyType.secondary.value
        })

        # Test 'az lbs account create'
        # Test to create an LocationBasedServices account
        account = self.cmd('az lbs account create -n {name} -g {rg} --sku {sku} -l {loc}', checks=[
            self.check('location', '{loc}'),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('sku.name', '{sku}')
        ]).get_output_in_json()

        # Call create again, expect to get the same account
        account_duplicated = self.cmd(
            'az lbs account create -n {name} -g {rg} --sku {sku} -l {loc}').get_output_in_json()
        self.assertEqual(account, account_duplicated)

        # Test 'az lbs account show'
        # Test to get information on LocationBasedServices account
        self.cmd('az lbs account show -n {name} -g {rg}', checks=[
            self.check('id', account['id']),
            self.check('location', '{loc}'),
            self.check('name', '{name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('sku.name', '{sku}')
        ])

        # Test 'az lbs account list'
        # Test to list all LocationBasedServices accounts under a resource group
        self.cmd('az lbs account list -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('type(@)', 'array'),
            self.check('[0].id', account['id']),
            self.check('[0].location', '{loc}'),
            self.check('[0].name', '{name}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].sku.name', '{sku}'),
            self.check('[0].tags', None)
        ])

        # Create two new accounts
        self.cmd('az lbs account create -n {name1} -g {rg} --sku {sku} -l {loc}')
        self.cmd('az lbs account create -n {name2} -g {rg} --sku {sku} -l {loc}')
        # Check that list command now shows three accounts.
        self.cmd('az lbs account list -g {rg}', checks=[
            self.check('length(@)', 3),
            self.check('type(@)', 'array'),
            self.check("length([?name == '{name}'])", 1),
            self.check("length([?name == '{name1}'])", 1),
            self.check("length([?name == '{name2}'])", 1),
            self.check("length([?resourceGroup == '{rg}'])", 3)
        ])

        # Test 'az lbs account key list'
        # Test to list keys for an LocationBasedServices account
        account_key_list = self.cmd('az lbs account key list -n {name} -g {rg}', checks=[
            self.check('id', account['id']),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        # Retrieve primary and secondary keys
        primary_key_old = account_key_list['primaryKey']
        secondary_key_old = account_key_list['secondaryKey']
        self.assertIsNotNone(primary_key_old)
        self.assertIsNotNone(secondary_key_old)

        # Test 'az lbs account key regenerate'
        # Test to change primary and secondary keys for an LocationBasedServices account
        key_regenerated = self.cmd('az lbs account key regenerate -n {name} -g {rg} -t {key_type_primary}', checks=[
            self.check('id', account['id']),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        # Only primary key was regenerated. Secondary key should remain same.
        self.assertNotEqual(primary_key_old, key_regenerated['primaryKey'])
        self.assertEqual(secondary_key_old, key_regenerated['secondaryKey'])

        # Save the new primary key, and regenerate the secondary key.
        primary_key_old = key_regenerated['primaryKey']
        key_regenerated = self.cmd(
            'az lbs account key regenerate -n {name} -g {rg} -t {key_type_secondary}').get_output_in_json()
        self.assertEqual(primary_key_old, key_regenerated['primaryKey'])
        self.assertNotEqual(secondary_key_old, key_regenerated['secondaryKey'])

        # Test 'az lbs account delete'
        # Test to remove an LocationBasedServices account
        self.cmd('az lbs account delete -n {name} -g {rg}', checks=self.is_empty())
        self.cmd('az lbs account show -n {name} -g {rg}', checks=self.is_empty())
        self.cmd('az lbs account list -g {rg}', checks=[
            self.check('length(@)', 2),
            self.check("length([?name == '{name}'])", 0)
        ])

        # Remove the rest of LocationBasedServices accounts
        exit_code = self.cmd('az lbs account delete -n {name1} -g {rg}').exit_code
        self.assertEqual(exit_code, 0)
        self.cmd('az lbs account delete -n {name2} -g {rg}')
        self.cmd('az lbs account list -g {rg}', checks=self.is_empty())
