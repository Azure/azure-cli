# AZURE CLI RBAC TEST DEFINITIONS
import json

from azure.cli.utils.command_test_script import CommandTestScript, JMESPathComparator

class RoleScenarioTest(CommandTestScript):

    def test_body(self):
        s = self
        scope = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590'
        role_def_id = 'de139f84-1756-47ae-9be6-808fbbe84772'
        full_role_def_id = '{}/providers/Microsoft.Authorization/roleDefinitions/{}'.format(scope, role_def_id)

        s.test('role list --scope {}'.format(scope),
            [
                JMESPathComparator("length([].contains(id, '{}')) == length(@)".format(scope), True)
            ])

        s.test('role show --scope {} --role-definition-id {}'.format(scope, role_def_id),
            {'name': role_def_id, 'properties' : {'roleName': 'Website Contributor', 'type': 'BuiltInRole'}})

        s.test('role show-by-id --role-definition-id {}'.format(full_role_def_id),
            {'name': role_def_id, 'properties' : {'roleName': 'Website Contributor', 'type': 'BuiltInRole'}})

    def __init__(self):
        super(RoleScenarioTest, self).__init__(None, self.test_body, None)

class RoleAssignmentScenarioTest(CommandTestScript):

    def test_body(self):
        s = self
        principal_id = '7a938a30-4226-420e-996f-4d48bca6d537'
        scope = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590'
        rg = 'travistestresourcegroup'
        resource = 'testsql23456/'
        parent_path = 'servers/testserver23456'

        list_all = s.run('role assignment list -o json')
        list_some = s.run('role assignment list --filter "principalId eq \'{}\'" '
                          '-o json'.format(principal_id))
        assert len(list_all) > len(list_some)

        s.test('role assignment list-for-scope --scope {}'.format(scope),
            [
                JMESPathComparator("length([].properties.contains(scope, '{}')) == length(@)".format(scope), True)
            ])

        id = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst39112/providers/Microsoft.Authorization/roleAssignments/b022bb45-7fc4-4125-b781-72b49c38ba18'
        res = s.run("role assignment show-by-id --role-assignment-id {} -o json".format(id))['id']
        assert res == id

    def __init__(self):
        super(RoleAssignmentScenarioTest, self).__init__(None, self.test_body, None)

ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'role_assignment_scenario',
        'script': RoleAssignmentScenarioTest()
    },
    {
        'test_name': 'role_scenario',
        'script': RoleScenarioTest()
    }
]

