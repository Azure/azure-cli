#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# AZURE CLI RBAC TEST DEFINITIONS
import mock
import re
import time

from azure.cli.utils.vcr_test_base import VCRTestBase, JMESPathCheck, ResourceGroupVCRTestBase, NoneCheck, MOCKED_SUBSCRIPTION_ID

class RoleScenarioTest(VCRTestBase):

    def test_role_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(RoleScenarioTest, self).__init__(__file__, test_method)

    def body(self):
        s = self
        scope = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590'
        role_def_id = 'de139f84-1756-47ae-9be6-808fbbe84772'
        role_resource_id = '{}/providers/Microsoft.Authorization/roleDefinitions/{}'.format(scope, role_def_id)

        s.cmd('role list'.format(scope),
            checks=JMESPathCheck("length([].contains(id, '{}')) == length(@)".format(scope), True))

        s.cmd('role show --role-id {}'.format(role_def_id), checks=[
            JMESPathCheck('name', role_def_id),
            JMESPathCheck('properties.roleName', 'Website Contributor'),
            JMESPathCheck('properties.type', 'BuiltInRole')
        ])

        s.cmd('role show --role-resource-id {}'.format(role_resource_id), checks=[
            JMESPathCheck('name', role_def_id),
            JMESPathCheck('properties.roleName', 'Website Contributor'),
            JMESPathCheck('properties.type', 'BuiltInRole')
        ])

        #TODO: when role creation is supported, test custom roles

class RoleAssignmentScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(RoleAssignmentScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'cli-role-assignment-test'
        self.user = 'testuser1@azuresdkteam.onmicrosoft.com'

    def set_up(self):
        super().set_up()
        self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {}'.format(self.user), None)
        time.sleep(15) #By-design, it takes some time for RBAC system propagated with graph object change

    def tear_down(self):
        self.cmd('ad user delete --upn-or-object-id {}'.format(self.user), None)
        super().tear_down()

    def test_role_assignment_scenario(self):
        if self.playback:
            return #live-only test, so far unable to replace guid in binary encoded body
        else:
            self.execute()

    def body(self):
        nsg_name = 'nsg1'
        self.cmd('network nsg create -n {} -g {}'.format(nsg_name, self.resource_group), None)
        result = self.cmd('network nsg show -n {} -g {}'.format(nsg_name, self.resource_group), None)
        resource_id = result['id']

        #test role assignments on a resource group
        self.cmd('role assignment create --assignee {} --role contributor -g {}'.format(self.user, self.resource_group), None)      
        self.cmd('role assignment list -g {}'.format(self.resource_group),
                 checks=[JMESPathCheck("length([])", 1)])
        self.cmd('role assignment list --assignee {} --role contributor -g {}'.format(self.user, self.resource_group),
                 checks=[JMESPathCheck("length([])", 1)])

        #test couple of more general filters
        result = self.cmd('role assignment list -g {} --include-inherited'.format(self.resource_group), None)
        self.assertTrue(len(result)>=1)

        result = self.cmd('role assignment list --all'.format(self.user, self.resource_group), None)
        self.assertTrue(len(result)>=1)

        self.cmd('role assignment delete --assignee {} --role contributor -g {}'.format(self.user, self.resource_group), None)
        self.cmd('role assignment list -g {}'.format(self.resource_group), checks=NoneCheck())

        #test role assignments on a resource
        self.cmd('role assignment create --assignee {} --role contributor --resource-id {}'.format(self.user, resource_id), None)
        self.cmd('role assignment list --assignee {} --role contributor --resource-id {}'.format(self.user, resource_id),
                 checks=[JMESPathCheck("length([])", 1)])
        self.cmd('role assignment delete --assignee {} --role contributor --resource-id {}'.format(self.user, resource_id), None)
        self.cmd('role assignment list --resource-id {}'.format(resource_id), checks=NoneCheck())

        #test role assignment on subscription level
        self.cmd('role assignment create --assignee {} --role reader'.format(self.user), None)
        self.cmd('role assignment list --assignee {} --role reader'.format(self.user),
                 checks=[JMESPathCheck("length([])", 1)])
        self.cmd('role assignment list --assignee {}'.format(self.user),
                 checks=[JMESPathCheck("length([])", 1)])
        self.cmd('role assignment delete --assignee {} --role reader'.format(self.user), None)
