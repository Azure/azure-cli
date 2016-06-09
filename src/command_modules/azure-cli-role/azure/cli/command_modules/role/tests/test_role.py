# AZURE CLI RBAC TEST DEFINITIONS
import json

from azure.cli.utils.vcr_test_base import VCRTestBase, JMESPathCheck

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

class RoleAssignmentScenarioTest(VCRTestBase):

    def test_role_assignment_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(RoleAssignmentScenarioTest, self).__init__(__file__, test_method)

    def body(self):
        s = self
        principal_id = '7a938a30-4226-420e-996f-4d48bca6d537'
        scope = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590'
        rg = 'travistestresourcegroup'
        resource = 'testsql23456/'
        parent_path = 'servers/testserver23456'

        list_all = s.cmd('role assignment list -o json')
        list_some = s.cmd('role assignment list --filter "principalId eq \'{}\'" -o json'.format(principal_id))
        assert len(list_all) > len(list_some)

        s.cmd('role assignment list-for-scope --scope {}'.format(scope),
            checks=JMESPathCheck("length([].properties.contains(scope, '{}')) == length(@)".format(scope), True))

        id = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst39112/providers/Microsoft.Authorization/roleAssignments/b022bb45-7fc4-4125-b781-72b49c38ba18'
        res = s.cmd("role assignment show-by-id --role-assignment-id {} -o json".format(id))['id']
        assert res == id
