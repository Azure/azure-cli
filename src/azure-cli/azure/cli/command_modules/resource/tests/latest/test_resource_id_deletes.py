# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import unittest
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer, live_only


@live_only()
class ResourceDeleteTests(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_delete_dependent_resources', location='southcentralus')
    def test_delete_dependent_resources(self, resource_group):
        vm_name = self.create_random_name('cli-test-vm', 30)
        tag_name = self.create_random_name('cli-test-tag', 20)
        username = 'ubuntu'
        password = self.create_random_name('Password#1', 30)

        self.cmd('vm create -n {} -g {} --image UbuntuLTS --tag {} '
                 '--admin-username {} --admin-password {} --authentication-type {} --nsg-rule None'
                 .format(vm_name, resource_group, tag_name, username, password, 'password'))

        rsrc_list = self.cmd('resource list --tag {} --query [].id'.format(tag_name)).get_output_in_json()
        self.cmd('resource delete --ids {}'.format(' '.join(rsrc_list)))
        self.cmd('resource wait --ids {} --deleted --timeout 300'.format(''.join(rsrc_list)))


if __name__ == '__main__':
    unittest.main()
