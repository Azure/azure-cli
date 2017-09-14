# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer


class ResourceDeleteTests(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_delete_dependent_resources')
    def test_delete_dependent_resources(self, resource_group):
        vm_name = self.create_random_name('cli-test-vm', 30)
        tag_name = self.create_random_name('cli-test-tag', 20)

        self.cmd('az vm create -n {} -g {} --image UbuntuLTS --tag {}'.format(vm_name, resource_group, tag_name))

        rsrc_list = self.cmd('az resource list --tag {} --query [].id'.format(tag_name)).get_output_in_json()

        delete_output = self.cmd('az resource delete --ids {}'.format(' '.join(rsrc_list))).get_output_in_json()

        self.assertTrue(len(rsrc_list) == len(delete_output))


if __name__ == '__main__':
    unittest.main()
