# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time
import unittest

from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer
from knack.util import CLIError


class CognitiveServicesTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_crud(self, resource_group):
        sname = self.create_random_name(prefix='cog', length=12)
        resource_location = 'westeurope'

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {} -g {} --kind {} --sku {} -l {} --yes'.format(
            sname, resource_group, 'Face', 'S0', resource_location), checks=[
            JMESPathCheck('name', sname),
            JMESPathCheck('location', resource_location),
            JMESPathCheck('sku.name', 'S0'),
            JMESPathCheck('provisioningState', 'Succeeded')])

        # test to show the details of cognitive services account
        self.cmd('az cognitiveservices account show -n {} -g {}'.format(
            sname, resource_group), checks=[
            JMESPathCheck('name', sname),
            JMESPathCheck('resourceGroup', resource_group)])

        # test to update the properties of cognitive servcies account
        tagname = self.create_random_name(prefix='tagname', length=10)
        tagvalue = self.create_random_name(prefix='tagvalue', length=10)
        self.cmd('az cognitiveservices account update -n {} -g {} --sku {} --tags {}'.format(
            sname, resource_group, 'S0', tagname + '=' + tagvalue), checks=[
            JMESPathCheck('sku.name', 'S0'),
            JMESPathCheck('tags', {tagname: tagvalue})])

        # test to list keys of a cogntive services account
        oldkeys = self.cmd('az cognitiveservices account keys list -n {} -g {}'.format(
            sname, resource_group), checks=[
            JMESPathCheck('length(key1)', 32),
            JMESPathCheck('length(key2)', 32)]).get_output_in_json()

        # test to regenerate the keys of a cognitive services account
        newkeys = self.cmd('az cognitiveservices account keys regenerate -n {} -g {} --key-name key1'.format(
            sname, resource_group)).get_output_in_json()
        assert oldkeys != newkeys

        # test to list cognitive service accounts under current resource group
        self.cmd('az cognitiveservices list -g {}'.format(resource_group), checks=[
            JMESPathCheck('length(@)', 1)])

        # test to delete the cognitive services account
        exitcode = self.cmd('az cognitiveservices account delete -n {} -g {}'.format(
            sname, resource_group)).exit_code
        assert exitcode == 0


if __name__ == '__main__':
    unittest.main()
