# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only

# ManagedServices RP has not been released to GA yet.
# It is expected to be released during the week of 7/15/2019.
# Until then we have to allow subscriptions to be able to use the functionality.
# We could have used the CLI test subscription but it had locks on it, which is not supported by the RP yet.
# So for the time being, tests are being marked record_only

name_prefix = 'climanagedservices'
tenant_id = 'bab3375b-6197-4a15-a44b-16c41faa91d7'
principal_id = 'd6f6c88a-5b7a-455e-ba40-ce146d4d3671'
role_definition_id = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
definition_id = 'afee244e-9a4d-41c9-a64d-8d7fc7124717'
msp_sub_id = '002b3477-bfbf-4402-b377-6003168b75d3'
assignment_id = 'b61427a6-974b-4987-a4cc-007a11ec8396'


class ManagedServicesTests(ScenarioTest):

    @record_only()
    def test_managedservices_commands(self):
        self.kwargs = {
            'name': self.create_random_name(prefix=name_prefix, length=24),
            'tenant-id': tenant_id,
            'principal-id': principal_id,
            'role-definition-id': role_definition_id,
            'header_parameters': {},
            'definition-id': definition_id,
            'subscription-id': msp_sub_id
        }

        # put definition
        self.cmd('az managedservices definition create --name {name} --tenant-id  {tenant-id} --principal-id {principal-id} --role-definition-id {role-definition-id} --definition-id {definition-id}',
                 checks=[
                     self.check('name', '{definition-id}'),
                     self.check('properties.provisioningState', 'Succeeded'),
                     self.check('properties.managedByTenantId', '{tenant-id}'),
                     self.check('properties.authorizations[0].roleDefinitionId', '{role-definition-id}'),
                     self.check('properties.authorizations[0].principalId', '{principal-id}')])

        # get definition
        self.cmd('az managedservices definition show --definition {definition-id}',
                 checks=[
                     self.check('name', '{definition-id}')])

        # registration assignment operation tests
        definition_resource_id = "/subscriptions/" + msp_sub_id + "/providers/Microsoft.ManagedServices/" \
                                                                  "registrationDefinitions/" \
                                                                + definition_id
        self.kwargs.update({
            'assignment-id': assignment_id,
            'registration-definition-resource-id': definition_resource_id
        })
        # put assignment
        self.cmd('az managedservices assignment  create --definition {registration-definition-resource-id} --assignment-id {assignment-id}',
                 checks=[
                     self.check('name', '{assignment-id}'),
                     self.check('properties.provisioningState', 'Succeeded')])

        # get assignment
        self.cmd('az managedservices assignment  show --assignment {assignment-id}',
                 checks=[
                     self.check('name', '{assignment-id}'), ])

        # delete assignment
        self.cmd('az managedservices assignment  delete --assignment {assignment-id}')

        # list assignments
        assignments_list = self.cmd('az managedservices assignment  list').get_output_in_json()
        assignments = []
        for assignment in assignments_list:
            name = assignment['name']
            assignments.append(name)
            self.assertTrue(assignment_id not in assignments)

        # delete definition
        self.cmd('az managedservices definition delete --definition {definition-id}')

        # list definitions
        definitions_list = self.cmd('az managedservices definition list').get_output_in_json()
        definitions = []
        for entry in definitions_list:
            name = entry['name']
            definitions.append(name)
        self.assertTrue(definition_id not in definitions)
