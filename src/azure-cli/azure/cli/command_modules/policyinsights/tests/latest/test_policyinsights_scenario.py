# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, create_random_name, record_only
from azure.cli.testsdk.exceptions import JMESPathCheckAssertionError

class PolicyInsightsTests(ScenarioTest):

    # Current recording was recorded against "Azure Governance Perf 24" (3593b919-b078-4cc1-902f-201232a97ac0)
    @record_only()
    @AllowLargeResponse(8192)
    def test_policy_insights(self):
        self.kwargs.update({
            'managementGroupId': 'azgovperftest',
            'rg': 'PSTestRG1',
            'keyVault': 'PSTestKV',
            'subnet': 'PSTestVN',
            'setDefinition': 'PSTestInitiative',
            'definition': 'PSTestDINEDefinition',
            'assignment': 'pstestdeployassignmentsub'
        })
        top_clause = '--top 2'
        filter_clause = '--filter "isCompliant eq false"'
        apply_clause = '--apply "groupby((policyAssignmentId, resourceId), aggregate($count as numRecords))"'
        select_clause = '--select "policyAssignmentId, resourceId, numRecords"'
        order_by_clause = '--order-by "numRecords desc"'
        from_clause = '--from "2022-04-01T00:00:00Z"'
        to_clause = '--to "2022-04-03T01:30:00Z"'
        scopes = [
            '-m {managementGroupId}',
            '',
            '-g {rg}',
            '--resource "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/{rg}/providers/microsoft.keyvault/vaults/{keyVault}"',
            '--resource "{keyVault}" --namespace "microsoft.keyvault" --resource-type "vaults" -g "{rg}"',
            '--resource "default" --namespace "microsoft.network" --resource-type "subnets" --parent "virtualnetworks/{subnet}" -g "{rg}"',
            '-s {setDefinition}',
            '-d {definition}',
            '-a {assignment}',
            '-a {assignment} -g {rg}'
        ]

        for scope in scopes:
            events = self.cmd('az policy event list {} {} {} {} {} {} {} {}'.format(
                scope,
                from_clause,
                to_clause,
                filter_clause,
                apply_clause,
                select_clause,
                order_by_clause,
                top_clause)).get_output_in_json()
            assert len(events) >= 0

            states = self.cmd('az policy state list {} {} {} {} {} {} {} {}'.format(
                scope,
                from_clause,
                to_clause,
                filter_clause,
                apply_clause,
                select_clause,
                order_by_clause,
                top_clause)).get_output_in_json()
            assert len(states) >= 0

            summary = self.cmd('az policy state summarize {} {} {} {} {}'.format(
                scope,
                from_clause,
                to_clause,
                filter_clause,
                top_clause)).get_output_in_json()
            assert summary["results"] is not None
            assert len(summary["policyAssignments"]) >= 0
            if len(summary["policyAssignments"]) > 0:
                assert summary["policyAssignments"][0]["results"] is not None
                assert len(summary["policyAssignments"][0]["policyDefinitions"]) >= 0
                if len(summary["policyAssignments"][0]["policyDefinitions"]) > 0:
                    assert summary["policyAssignments"][0]["policyDefinitions"][0]["results"] is not None

        states = self.cmd('az policy state list {} {} {}'.format(
            scopes[3],
            '--expand PolicyEvaluationDetails',
            top_clause
        ), checks=[
            self.check('length([?complianceState==`NonCompliant`].policyEvaluationDetails)', 2)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_triggerscan')
    def test_policy_insights_triggerscan(self):
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
            'bip': '96670d01-0a4d-4649-9c89-2d3abc0a5025'
        })

        # create a subscription policy assignment that we can get an updated compliance state for
        self.cmd(
            'policy assignment create --policy {bip} -n {pan} --resource-group {rg} -p \'{{ "tagName": {{ "value": "notThere" }} }}\'')

        # trigger a subscription scan and do not wait for it to complete
        self.cmd('policy state trigger-scan --no-wait', checks=[
            self.is_empty()
        ])

        # trigger a resource group scan and wait for it to complete
        self.cmd('policy state trigger-scan -g {rg}', checks=[
            self.is_empty()
        ])

        # ensure the compliance state of the resource group was updated
        self.cmd('policy state list -g {rg} -a {pan} --filter \"isCompliant eq false\"', checks=[
            self.check("length([])", 1)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_remediation')
    @StorageAccountPreparer(name_prefix='cliremediation')
    def test_policy_insights_remediation(self, resource_group_location, storage_account):
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
            'rn': self.create_random_name('azurecli-test-remediation', 40),
            'bip': '06a78e20-9358-41c9-923c-fb736d382a4d',
            'location': resource_group_location,
            'sa': storage_account
        })

        # create a subscription policy assignment that we can trigger remediations on
        assignment = self.cmd('policy assignment create --policy {bip} -n {pan}').get_output_in_json()
        self.kwargs['pid'] = assignment['id'].lower()

        try:
            # create a remediation at resource group scope
            self.cmd('policy remediation create -n {rn} -g {rg} -a {pan}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', '{rg}'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation show -n {rn} -g {rg}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', '{rg}'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation list -g {rg}', checks=[
                self.check("length([?name == '{rn}'])", 1),
            ])

            self.cmd('policy remediation deployment list -n {rn} -g {rg}', checks=[
                self.is_empty()
            ])

            self.cmd('policy remediation delete -n {rn} -g {rg}')

            self.cmd('policy remediation list -g {rg}', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])

            # create a remediation at subscription scope with location filters
            self.cmd('policy remediation create -n {rn} -a {pan} --location-filters {location}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', None),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters.locations[*] | length([])', 1),
                self.check('filters.locations[0]', '{location}'),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation show -n {rn}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', None),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters.locations[*] | length([])', 1),
                self.check('filters.locations[0]', '{location}'),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation list', checks=[
                self.check("length([?name == '{rn}'])", 1),
            ])

            self.cmd('policy remediation deployment list -n {rn}', checks=[
                self.is_empty()
            ])

            self.cmd('policy remediation delete -n {rn}')

            self.cmd('policy remediation list', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])

            # create a remediation at individual resource scope
            self.cmd('policy remediation create -n {rn} -a {pan} -g {rg} --namespace "Microsoft.Storage" --resource-type storageAccounts --resource {sa}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', '{rg}'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation show -n {rn} -g {rg} --namespace "Microsoft.Storage" --resource-type storageAccounts --resource {sa}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', '{rg}'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation list -g {rg} --namespace "Microsoft.Storage" --resource-type storageAccounts --resource {sa}', checks=[
                self.check("length([?name == '{rn}'])", 1),
            ])

            self.cmd('policy remediation deployment list -n {rn} -g {rg} --namespace "Microsoft.Storage" --resource-type storageAccounts --resource {sa}', checks=[
                self.is_empty()
            ])

            self.cmd('policy remediation delete -n {rn} -g {rg} --namespace "Microsoft.Storage" --resource-type storageAccounts --resource {sa}')

            self.cmd('policy remediation list -g {rg} --namespace "Microsoft.Storage" --resource-type storageAccounts --resource {sa}', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])
        finally:
            self.cmd('policy assignment delete -n {pan}')

    @AllowLargeResponse()
    def test_policy_insights_remediation_policy_set(self):
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
            'psn': self.create_random_name('azurecli-test-policy-set', 40),
            'rn': self.create_random_name('azurecli-test-remediation', 40),
            'drid': self.create_random_name('cli-test-reference-id', 40),
            'bip': '/providers/microsoft.authorization/policyDefinitions/06a78e20-9358-41c9-923c-fb736d382a4d'
        })

        try:
            # create a policy set that will be remediated
            self.cmd('policy set-definition create -n {psn} --definitions "[{{ \\"policyDefinitionId\\": \\"{bip}\\", \\"policyDefinitionReferenceId\\": \\"{drid}\\" }}]"')

            # create a subscription policy assignment that we can trigger remediations on
            assignment = self.cmd('policy assignment create --policy-set-definition {psn} -n {pan}').get_output_in_json()
            self.kwargs['pid'] = assignment['id'].lower()

            # create a remediation at subscription scop
            self.cmd('policy remediation create -n {rn} -a {pan} --definition-reference-id {drid}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', None),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', '{drid}'),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation show -n {rn}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', None),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', '{drid}'),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation list', checks=[
                self.check("length([?name == '{rn}'])", 1),
            ])

            self.cmd('policy remediation deployment list -n {rn}', checks=[
                self.is_empty()
            ])

            self.cmd('policy remediation delete -n {rn}')

            self.cmd('policy remediation list', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])
        finally:
            self.cmd('policy assignment delete -n {pan}')
            self.cmd('policy set-definition delete -n {psn}')

    # This is record only since MG auth can take a while to propagate and management groups can be disruptive
    @record_only()
    def test_policy_insights_remediation_management_group(self):
        self.kwargs.update({
            'pan': self.create_random_name('cli-test-pa', 23),
            'rn': self.create_random_name('cli-test-remediation', 30),
            'mg': 'cli-test-mg',
            'bip': '06a78e20-9358-41c9-923c-fb736d382a4d'
        })

        # create a management group we can assign policy to
        self.cmd('account management-group create -n {mg}')
        time.sleep(20)
        management_group = self.cmd(
            'account management-group show --name cli-test-mg').get_output_in_json()
        

        try:
            # create a policy assignment that we can trigger remediations on
            self.kwargs['mgid'] = management_group['id']
            assignment = self.cmd('policy assignment create --scope {mgid} --policy {bip} -n {pan}').get_output_in_json()
            self.kwargs['pid'] = assignment['id'].lower()

            # create a remediation at management group scope
            self.cmd('policy remediation create -n {rn} -m {mg} -a {pid}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('resourceGroup', None),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation show -n {rn} -m {mg}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('resourceGroup', None),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            self.cmd('policy remediation list -m {mg}', checks=[
                self.check("length([?name == '{rn}'])", 1),
            ])

            self.cmd('policy remediation deployment list -n {rn} -m {mg}', checks=[
                self.is_empty()
            ])

            self.cmd('policy remediation delete -n {rn} -m {mg}')

            self.cmd('policy remediation list -m {mg}', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])
        finally:
            self.cmd('policy assignment delete -n {pan} --scope {mgid}')
            self.cmd('account management-group delete -n {mg}')

    # Executing a real remediation requires more time-intensive setup than can be done in a live scenario test.
    # This record_only test executes a real remediation against a known non-compliant policy
    # Test setup required for running the test live:
    #    1. Create a resource group by name 'az-cli-policy-insights-test'
    #    2. Create 2 storage accounts in two different regions in above RG
    #    3. At above RG scope, create a new policy assignment for built-in definition with name '361c2074-3595-4e5d-8cab-4f21dffc835c' and display name 'Deploy Advanced Threat Protection on storage accounts'
    #    4. Update the 'pan' key value in test code below with the assignment name created above
    #    5. Trigger an on-demand evaluation scan on above RG by calling triggerEvaluation API. Check https://docs.microsoft.com/en-us/azure/governance/policy/how-to/get-compliance-data#on-demand-evaluation-scan
    #    6. After step 5 completes, you should see the two storage accounts listed as non-compliant resources for the above assignment
    #    7. Now run the testcase in live mode using command 'azdev test test_policy_insights_remediation_complete --live'
    @record_only()
    @AllowLargeResponse(8192)
    def test_policy_insights_remediation_complete(self):
        self.kwargs.update({
            'pan': '78447a35ea2b4b14b701dae0',
            'rg': 'az-cli-policy-insights-test',
            'rn': self.create_random_name('azurecli-test-remediation', 40)
        })

        assignment = self.cmd('policy assignment show -g {rg} -n {pan}').get_output_in_json()
        self.kwargs['pid'] = assignment['id'].lower()

        # create a remediation at resource group scope
        self.cmd('policy remediation create -n {rn} -g {rg} -a {pan}', checks=[
            self.check('name', '{rn}'),
            self.check('resourceGroup', '{rg}'),
            self.check('policyAssignmentId', '{pid}'),
            self.check('policyDefinitionReferenceId', None),
            self.check('filters', None),
            self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
        ])

        for i in range(5):
            try:
                self.cmd('policy remediation show -n {rn} -g {rg}', checks=[
                    self.check('name', '{rn}'),
                    self.check('resourceGroup', '{rg}'),
                    self.check('policyAssignmentId', '{pid}'),
                    self.check('deploymentStatus.totalDeployments', 2),
                    self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
                ])
                break
            except JMESPathCheckAssertionError:
                time.sleep(5)

        self.cmd('policy remediation list -g {rg}', checks=[
            self.check("length([?name == '{rn}'])", 1)
        ])

        self.cmd('policy remediation deployment list -n {rn} -g {rg}', checks=[
            self.check('length([])', 2),
            self.exists('[0].createdOn'),
            self.exists('[0].lastUpdatedOn'),
            self.exists('[0].resourceLocation'),
            self.exists('[0].status'),
            self.check("length([?contains(@.remediatedResourceId, '/resourcegroups/{rg}/providers/microsoft.storage/storageaccounts')])", 2)
        ])

        # cancel the remediation
        self.cmd('policy remediation cancel -n {rn} -g {rg}', checks=[
            self.check('provisioningState', 'Cancelling')
        ])

    # Test a remediation that re-evaluates compliance results before remediating
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_remediation')
    @StorageAccountPreparer(name_prefix='cliremediation')
    def test_policy_insights_remediation_reevaluate(self, resource_group_location, storage_account):
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
            'rn': self.create_random_name('azurecli-test-remediation', 40),
            'bip': '5ffd78d9-436d-4b41-a421-5baa819e3008',
            'location': resource_group_location,
            'sa': storage_account
        })

        # create a resource group policy assignment that we can trigger remediations on
        assignment = self.cmd(
            'policy assignment create --policy {bip} -g {rg} -n {pan} --location {location} --assign-identity -p \'{{"tagName": {{ "value": "cliTagKey" }}, "tagValue": {{ "value": "cliTagValue" }} }}\'').get_output_in_json()
        self.kwargs['pid'] = assignment['id'].lower()

        # create a remediation at resource group scope that will re-evaluate compliance
        self.cmd('policy remediation create -n {rn} -g {rg} -a {pan} --resource-discovery-mode ReEvaluateCompliance', checks=[
            self.check('name', '{rn}'),
            self.check('provisioningState', 'Accepted'),
            self.check('resourceGroup', '{rg}'),
            self.check('policyAssignmentId', '{pid}'),
            self.check('policyDefinitionReferenceId', None),
            self.check('filters', None),
            self.check('deploymentStatus.totalDeployments', 0),
            self.check('resourceDiscoveryMode', 'ReEvaluateCompliance')
        ])

        self.cmd('policy remediation show -n {rn} -g {rg}', checks=[
            self.check('name', '{rn}'),
            self.check_pattern('provisioningState', '(?:Evaluating|Accepted)'),
            self.check('resourceGroup', '{rg}'),
            self.check('policyAssignmentId', '{pid}'),
            self.check('deploymentStatus.totalDeployments', 0),
            self.check('resourceDiscoveryMode', 'ReEvaluateCompliance')
        ])

        self.cmd('policy remediation list -g {rg}', checks=[
            self.check("length([?name == '{rn}'])", 1)
        ])

        self.cmd('policy remediation deployment list -n {rn} -g {rg}', checks=[
            self.check('length([])', 0)
        ])

        # cancel the remediation
        self.cmd('policy remediation cancel -n {rn} -g {rg}', checks=[
            self.check('provisioningState', 'Cancelling')
        ])

    @AllowLargeResponse(8192)
    def test_policy_insights_metadata(self):
        # Get all metadata resources
        all_metadata_resources = self.cmd('policy metadata list').get_output_in_json()
        assert len(all_metadata_resources) > 1

        # Test the --top argument
        assert len(self.cmd('policy metadata list --top 0').get_output_in_json()) == 0

        top_metadata_resources = self.cmd('policy metadata list --top {}'.format(len(all_metadata_resources) + 1)).get_output_in_json()
        assert len(top_metadata_resources) == len(all_metadata_resources)

        top_metadata_resources = self.cmd('policy metadata list --top {}'.format(len(all_metadata_resources) - 1)).get_output_in_json()
        assert len(top_metadata_resources) == len(all_metadata_resources) - 1

        # Test getting an individual resouce
        resource_metadata_name = top_metadata_resources[0]['name']
        metadata_resource = self.cmd('policy metadata show --name {}'.format(resource_metadata_name)).get_output_in_json()
        assert metadata_resource['name'] == resource_metadata_name

        metadata_resource = self.cmd('policy metadata show -n {}'.format(resource_metadata_name)).get_output_in_json()
        assert metadata_resource['name'] == resource_metadata_name
