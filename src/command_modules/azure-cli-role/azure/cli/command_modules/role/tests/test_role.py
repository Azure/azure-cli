#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# AZURE CLI RBAC TEST DEFINITIONS
import mock
import time

from azure.cli.utils.vcr_test_base import VCRTestBase, JMESPathCheck, ResourceGroupVCRTestBase

class RoleScenarioTest(VCRTestBase):

    def test_role_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(RoleScenarioTest, self).__init__(__file__, test_method)

    def body(self):
        s = self
        scope = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590'
        role_def_id = 'de139f84-1756-47ae-9be6-808fbbe84772'
        full_role_def_id = '{}/providers/Microsoft.Authorization/roleDefinitions/{}'.format(scope, role_def_id)

        s.cmd('role list --scope {}'.format(scope),
            checks=JMESPathCheck("length([].contains(id, '{}')) == length(@)".format(scope), True))

        s.cmd('role show --scope {} --role-definition-id {}'.format(scope, role_def_id), checks=[
            JMESPathCheck('name', role_def_id),
            JMESPathCheck('properties.roleName', 'Website Contributor'),
            JMESPathCheck('properties.type', 'BuiltInRole')
        ])

        s.cmd('role show-by-id --role-definition-id {}'.format(full_role_def_id), checks=[
            JMESPathCheck('name', role_def_id),
            JMESPathCheck('properties.roleName', 'Website Contributor'),
            JMESPathCheck('properties.type', 'BuiltInRole')
        ])

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
            #TODO: we should auto record generated guids and use them under playback.
            #For now, get the values from the .yaml file and put in here.
            with mock.patch('uuid.uuid4') as m:
                m.side_effect = ['1518cef5-a2c8-48e1-acb5-eaadf2474f79', 'f13b65c4-7c62-4dd2-b2eb-2a348b57c25b']
                self.execute()
        else:
            self.execute()

    def body(self):       
        nsg_name = 'nsg1'
        self.cmd('network nsg create -n {} -g {}'.format(nsg_name, self.resource_group), None)
        result = self.cmd('network nsg show -n {} -g {}'.format(nsg_name, self.resource_group), None)
        resource_id = result['id']

        #test role assignments on a resource group
        result = self.cmd('role assignment create --assignee {} --role contributor -g {}'.format(self.user, self.resource_group), None)
        scope = result['properties']['scope']
        self.cmd('role assignment list-for-resource-group -g {}'.format(self.resource_group),
                 checks=[JMESPathCheck("length([?properties.scope == '{}'])".format(scope), 1)])
        self.cmd('role assignment delete -n {} --scope {}'.format(result['name'], result['properties']['scope']), None)
        self.cmd('role assignment list-for-resource-group -g {}'.format(self.resource_group),
                 checks=[JMESPathCheck("length([?properties.scope == '{}'])".format(scope), 0)])

        #test role assignments on a resource
        result2 = self.cmd('role assignment create --assignee {} --role contributor --resource-id {}'.format(self.user, resource_id), None)
        scope = result2['properties']['scope']
        self.cmd('role assignment list-for-scope --scope {}'.format(scope),
                 checks=[JMESPathCheck("length([?properties.scope == '{}'])".format(scope), 1)])
        self.cmd('role assignment delete -n {} --scope {}'.format(result2['name'], scope), None)
        self.cmd('role assignment list-for-scope --scope {}'.format(scope),
                 checks=[JMESPathCheck("length([?properties.scope == '{}'])".format(scope), 0)])

        #TODO: test role assignment on subscription level will be done after the 'list' command gets improved