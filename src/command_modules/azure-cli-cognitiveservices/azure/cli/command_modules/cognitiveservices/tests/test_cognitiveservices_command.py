# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from knack.util import CLIError


class CognitiveServicesTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_crud(self, resource_group):
        sname = self.create_random_name(prefix='cog', length=12)
        tagname = self.create_random_name(prefix='tagname', length=15)
        tagvalue = self.create_random_name(prefix='tagvalue', length=15)

        self.kwargs.update({
            'sname': sname,
            'kind': 'Face',
            'sku': 'S0',
            'location': 'westeurope',
            'tags': tagname + '=' + tagvalue
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('provisioningState', 'Succeeded')])

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
        newkeys = self.cmd('az cognitiveservices account keys regenerate -n {sname} -g {rg} --key-name key1').get_output_in_json()  # pylint: disable=line-too-long
        self.assertNotEqual(oldkeys, newkeys)

        # test to list cognitive service accounts under current resource group
        self.cmd('az cognitiveservices list -g {rg}', checks=[
            self.check('length(@)', 1)])

        # test to delete the cognitive services account
        exitcode = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}').exit_code
        self.assertEqual(exitcode, 0)


if __name__ == '__main__':
    unittest.main()
