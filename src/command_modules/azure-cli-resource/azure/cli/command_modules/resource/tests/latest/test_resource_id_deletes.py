# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer, live_only


class ResourceDeleteTests(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_delete_dependent_resources', location='southcentralus')
    def test_delete_dependent_resources(self, resource_group):
        vm_name = self.create_random_name('cli-test-vm', 30)
        tag_name = self.create_random_name('cli-test-tag', 20)
        username = 'ubuntu'
        password = self.create_random_name('Password#1', 30)

        self.cmd('vm create -n {} -g {} --image UbuntuLTS --tag {} '
                 '--admin-username {} --admin-password {} --authentication-type {}'
                 .format(vm_name, resource_group, tag_name, username, password, 'password'))

        rsrc_list = self.cmd('resource list --tag {} --query [].id'.format(tag_name)).get_output_in_json()
        self.cmd('resource delete --ids {}'.format(' '.join(rsrc_list)))
        for _ in range(30):
            time.sleep(10)
            leftovers = self.cmd('resource list --tag {}'.format(tag_name)).get_output_in_json()
            if not leftovers:
                return
        self.fail('Failed to delete all resources as we are still seeing a few leftovers:' + str(leftovers))

if __name__ == '__main__':
    unittest.main()
