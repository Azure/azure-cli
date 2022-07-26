# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from knack.util import CLIError


class CognitiveServicesTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_crud(self, resource_group):
        sname = self.create_random_name(prefix='cog', length=12)
        tagname = self.create_random_name(prefix='tagname', length=15)
        tagvalue = self.create_random_name(prefix='tagvalue', length=15)

        self.kwargs.update({
            'sname': sname,
            'kind': 'FormRecognizer',
            'sku': 'S0',
            'location': 'centraluseuap',
            'tags': tagname + '=' + tagvalue
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])

        # test to show the details of cognitive services account
        self.cmd('az cognitiveservices account show -n {sname} -g {rg}',
                 checks=[self.check('name', '{sname}'),
                         self.check('resourceGroup', '{rg}')])

        # test to update the properties of cognitive services account
        self.cmd('az cognitiveservices account update -n {sname} -g {rg} --sku {sku} --tags {tags}',
                 checks=[self.check('sku.name', '{sku}'),
                         self.check('tags', {tagname: tagvalue})])

        # test to list keys of a cogntive services account
        oldkeys = self.cmd('az cognitiveservices account keys list -n {sname} -g {rg}',
                           checks=[self.check('length(key1)', 32),
                                   self.check('length(key2)', 32)]).get_output_in_json()

        # test to regenerate the keys of a cognitive services account
        newkeys = self.cmd('az cognitiveservices account keys regenerate -n {sname} -g {rg} --key-name Key1').get_output_in_json()  # pylint: disable=line-too-long
        self.assertNotEqual(oldkeys, newkeys)

        # test to list cognitive service accounts under current resource group
        self.cmd('az cognitiveservices account list -g {rg}', checks=[
            self.check('length(@)', 1)])

        # test to delete the cognitive services account
        exitcode = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}').exit_code
        self.assertEqual(exitcode, 0)

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_cognitiveservices_account_list_kinds(self, resource_group):
        # test to list cognitive services account kinds
        results = self.cmd('az cognitiveservices account list-kinds').get_output_in_json()
        self.assertTrue(len(results) > 0)
        self.assertTrue('Face' in results)

    @ResourceGroupPreparer()
    def test_cognitiveservices_account_list_skus_legacy(self, resource_group):

        self.kwargs.update({
            'name': self.create_random_name(prefix='cs_cli_test_', length=16),
            'kind': 'FormRecognizer',
            'sku': 'S0',
            'location': 'centraluseuap'
        })

        self.cmd('az cognitiveservices account create -n {name} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{name}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])

        results = self.cmd('az cognitiveservices account list-skus -n {name} -g {rg}').get_output_in_json()
        self.assertTrue(isinstance(results['value'], list))
        self.assertTrue(len(results['value']) > 0)

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_cognitiveservices_account_list_skus(self, resource_group):

        self.kwargs.update({
            'kind': 'Face',
            'location': 'westus'
        })

        results = self.cmd('az cognitiveservices account list-skus --kind {kind}').get_output_in_json()
        self.assertTrue(isinstance(results, list))
        self.assertTrue(len(results) > 0)

        for sku in results:
            self.assertTrue(sku['kind'] == self.kwargs['kind'])

        results = self.cmd('az cognitiveservices account list-skus --kind {kind} --location {location}').get_output_in_json()
        self.assertTrue(isinstance(results, list))
        self.assertTrue(len(results) > 0)

        for sku in results:
            self.assertTrue(sku['kind'] == self.kwargs['kind'])
            self.assertTrue(self.kwargs['location'].lower() in [x.lower() for x in sku['locations']])

    @ResourceGroupPreparer()
    def test_cognitiveservices_account_list_usage(self, resource_group):

        self.kwargs.update({
            'name': self.create_random_name(prefix='cs_cli_test_', length=16),
            'kind': 'TextAnalytics',
            'sku': 'S',
            'location': 'westeurope'
        })

        self.cmd('az cognitiveservices account create -n {name} -g {rg} --kind {kind} --sku {sku} -l {location}',
                 checks=[self.check('name', '{name}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])

        results = self.cmd('az cognitiveservices account list-usage -n {name} -g {rg}').get_output_in_json()
        self.assertTrue(isinstance(results, list))


if __name__ == '__main__':
    unittest.main()
