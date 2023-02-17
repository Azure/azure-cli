# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, create_random_name, record_only
from azure.cli.testsdk.exceptions import JMESPathCheckAssertionError
from .test_utils import AttestationConstants as C


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
                assert len(summary["policyAssignments"]
                           [0]["policyDefinitions"]) >= 0
                if len(summary["policyAssignments"][0]["policyDefinitions"]) > 0:
                    assert summary["policyAssignments"][0]["policyDefinitions"][0]["results"] is not None

        states = self.cmd('az policy state list {} {} {}'.format(
            scopes[3],
            '--expand PolicyEvaluationDetails',
            top_clause
        ), checks=[
            self.check(
                'length([?complianceState==`NonCompliant`].policyEvaluationDetails)', 2)
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
        assignment = self.cmd(
            'policy assignment create --policy {bip} -n {pan}').get_output_in_json()
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

            self.cmd(
                'policy remediation delete -n {rn} -g {rg} --namespace "Microsoft.Storage" --resource-type storageAccounts --resource {sa}')

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
            self.cmd(
                'policy set-definition create -n {psn} --definitions "[{{ \\"policyDefinitionId\\": \\"{bip}\\", \\"policyDefinitionReferenceId\\": \\"{drid}\\" }}]"')

            # create a subscription policy assignment that we can trigger remediations on
            assignment = self.cmd(
                'policy assignment create --policy-set-definition {psn} -n {pan}').get_output_in_json()
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
            assignment = self.cmd(
                'policy assignment create --scope {mgid} --policy {bip} -n {pan}').get_output_in_json()
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

        assignment = self.cmd(
            'policy assignment show -g {rg} -n {pan}').get_output_in_json()
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
            self.check(
                "length([?contains(@.remediatedResourceId, '/resourcegroups/{rg}/providers/microsoft.storage/storageaccounts')])", 2)
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
        all_metadata_resources = self.cmd(
            'policy metadata list').get_output_in_json()
        assert len(all_metadata_resources) > 1

        # Test the --top argument
        assert len(
            self.cmd('policy metadata list --top 0').get_output_in_json()) == 0

        top_metadata_resources = self.cmd(
            'policy metadata list --top {}'.format(len(all_metadata_resources) + 1)).get_output_in_json()
        assert len(top_metadata_resources) == len(all_metadata_resources)

        top_metadata_resources = self.cmd(
            'policy metadata list --top {}'.format(len(all_metadata_resources) - 1)).get_output_in_json()
        assert len(top_metadata_resources) == len(all_metadata_resources) - 1

        # Test getting an individual resouce
        resource_metadata_name = top_metadata_resources[0]['name']
        metadata_resource = self.cmd(
            'policy metadata show --name {}'.format(resource_metadata_name)).get_output_in_json()
        assert metadata_resource['name'] == resource_metadata_name

        metadata_resource = self.cmd(
            'policy metadata show -n {}'.format(resource_metadata_name)).get_output_in_json()
        assert metadata_resource['name'] == resource_metadata_name

    # Test policy attestation CRUD requests at various scopes
    @record_only()
    @AllowLargeResponse()
    def test_policy_attestation(self):
        self._test_policy_insights_attestation_sub()
        self._test_policy_insights_attestation_resource()
        self._test_policy_insights_attestation_rg()
        self._test_policy_insights_attestation_collection()

    def _test_policy_insights_attestation_rg(self):
        self.kwargs.update({
            'pan': C.MANUAL_POLICY_RG_ASSIGNMENT,
            'rn': self.create_random_name('azurecli-test-attestation', 40),
            'rg': C.ATTESTATION_TEST_RG_NAME,
            'initiative_id': C.MANUAL_POLICY_RG_INITIATIVE_ASSIGNMENT,
            'ref_id': C.MANUAL_POLICY_RG_INITIATIVE_REFID
        })

        try:
            assignment = self.cmd(
                'policy assignment show -n {pan}').get_output_in_json()
            self.kwargs['pid'] = assignment['id'].lower()

            # region Policy Attestation RG CRUD minimal

            # create a minimal attestation at resource group scope
            self.cmd(
                'policy attestation create --attestation-name {rn} -g {rg} -a {pan}', checks=self._check_create_attestation_common())

            # get the attestation at resource group scope
            self.cmd(
                'policy attestation show --attestation-name {rn} -g {rg}', checks=self._check_create_attestation_common())

            # update the attestation at resource group scope
            self.kwargs['comments'] = 'Adding a comment'
            self.cmd("policy attestation update --attestation-name {rn} -g {rg} --comments '{comments}'", checks=[
                     self.check('comments', '{comments}')] + self._check_create_attestation_common())

            # delete an attestation at resource group scope
            self.cmd(
                'policy attestation delete --attestation-name {rn} -g {rg}')

            self.cmd('policy attestation list -g {rg}', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])
            # endregion

            # region Policy Attestation RG CRUD Full

            self.kwargs.update({
                "assessment_date": "2023-01-01T08:29:18Z",
                'rn': self.create_random_name('azurecli-test-attestation', 40),
                "compliance_state": "Compliant",
                "evidence1": "source-uri=https://sampleuri.com description='Sample description for the sample uri'",
                "evidence2": "source-uri=https://sampleuri2.com description='Sample description 2 for the sample uri 2'",
                "expires_on": "2024-08-01T05:29:18Z",
                "owner": "user@microsoft.com",
                "metadata": "Location=NYC Dept=ACC"
            })

            assignment = self.cmd(
                'policy assignment show -n {initiative_id}').get_output_in_json()
            self.kwargs['pid'] = assignment['id'].lower()

            # create an attestation with all the properties at RG scope.
            self.cmd(
                "policy attestation create --attestation-name {rn} -g {rg} -a {initiative_id} --compliance-state {compliance_state} --assessment-date '{assessment_date}' --evidence {evidence1} --evidence {evidence2} --expires-on '{expires_on}' --owner {owner} --metadata {metadata} --definition-reference-id '{ref_id}' --debug", checks=self._check_attestation_properties())

            # get the attestation at resource group scope
            self.cmd(
                'policy attestation show --attestation-name {rn} -g {rg}', checks=self._check_attestation_properties())

            self.cmd(
                'policy attestation delete --attestation-name {rn} -g {rg}')

            self.cmd('policy attestation list -g {rg}', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])
            # endregion
        finally:
            self._delete_all_attestations()

    def _test_policy_insights_attestation_sub(self):
        self.kwargs.update({
            'pan': C.MANUAL_POLICY_SUB_ASSIGNMENT,
            'rn': self.create_random_name('azurecli-test-attestation', 40),
            'initiative_id': C.MANUAL_POLICY_SUB_INITIATIVE_ASSIGNMENT,
            'ref_id': C.MANUAL_POLICY_SUB_INITIATIVE_REFID
        })

        try:
            assignment = self.cmd(
                'policy assignment show -n {pan}').get_output_in_json()
            self.kwargs['pid'] = assignment['id'].lower()

            # region Policy Attestation Subscription CRUD minimal

            # create a minimal attestation at subscription scope
            self.cmd(
                'policy attestation create --attestation-name {rn} -a {pan}', checks=self._check_create_attestation_common())

            # get the attestation at subscription scope
            self.cmd(
                'policy attestation show --attestation-name {rn}', checks=self._check_create_attestation_common())

            # update the attestation at subscription scope
            self.kwargs['comments'] = 'Adding a comment'
            self.cmd("policy attestation update --attestation-name {rn} --comments '{comments}'", checks=[
                     self.check('comments', '{comments}')] + self._check_create_attestation_common())

            # delete an attestation at subscription scope
            self.cmd('policy attestation delete --attestation-name {rn}')

            # verify that the attestation has been deleted.
            self.cmd('policy attestation list', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])
            # endregion

            # region Policy Attestation Subscription CRUD Full

            self.kwargs.update({
                "assessment_date": "2023-01-01T08:29:18Z",
                'rn': self.create_random_name('azurecli-test-attestation', 40),
                "compliance_state": "Compliant",
                "evidence1": "source-uri=https://sampleuri.com description='Sample description for the sample uri'",
                "evidence2": "source-uri=https://sampleuri2.com description='Sample description 2 for the sample uri 2'",
                "expires_on": "2024-08-01T05:29:18Z",
                "owner": "user@microsoft.com",
                "metadata": "Location=NYC Dept=ACC"
            })

            assignment = self.cmd(
                'policy assignment show -n {initiative_id}').get_output_in_json()
            self.kwargs['pid'] = assignment['id'].lower()

            self.cmd(
                "policy attestation create --attestation-name {rn} -a {initiative_id} --compliance-state {compliance_state} --assessment-date '{assessment_date}' --evidence {evidence1} --evidence {evidence2} --expires-on '{expires_on}' --owner {owner} --metadata {metadata} --definition-reference-id '{ref_id}'", checks=self._check_attestation_properties())

            # get the attestation at subscription scope
            self.cmd(
                'policy attestation show --attestation-name {rn}', checks=self._check_attestation_properties())

            # delete the attestation.
            self.cmd('policy attestation delete --attestation-name {rn}')

            # verify that the attestation has been deleted.
            self.cmd('policy attestation list', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])
            # endregion
        finally:
            self._delete_all_attestations()

    def _test_policy_insights_attestation_resource(self):
        self.kwargs.update({
            'pan': C.MANUAL_POLICY_RESOURCE_ASSIGNMENT,
            'rn': self.create_random_name('azurecli-test-attestation', 40),
            'resource_name': C.ATTESTATION_TEST_RESOURCE_NAME,
            'rg': C.ATTESTATION_TEST_RG_NAME,
            'initiative_id': C.MANUAL_POLICY_RESOURCE_INITIATIVE_ASSIGNMENT,
            'ref_id': C.MANUAL_POLICY_RESOURCE_INITIATIVE_REFID
        })

        try:
            assignment = self.cmd(
                'policy assignment show -n {pan}').get_output_in_json()
            self.kwargs['pid'] = assignment['id'].lower()

            # region Policy Attestation Resource CRUD minimal

            vnet = self.cmd(
                "network vnet show -n '{resource_name}' -g {rg}").get_output_in_json()
            self.kwargs['resource_id'] = vnet['id'].lower()
            # create a minimal attestation at resource scope
            self.cmd(
                "policy attestation create --attestation-name {rn} -a {pan} --resource '{resource_id}'", checks=self._check_create_attestation_common())

            # get the attestation at resource scope
            self.cmd("policy attestation show --attestation-name {rn} --resource '{resource_id}'", checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('policyDefinitionReferenceId', None),
                self.check('policyAssignmentId', '{pid}')
            ])

            # update the attestation at resource scope
            self.kwargs['comments'] = 'Adding a comment'
            self.cmd("policy attestation update --attestation-name {rn} --comments '{comments}' --resource '{resource_id}'", checks=[
                     self.check('comments', '{comments}')] + self._check_create_attestation_common())

            # delete an attestation at resource scope
            self.cmd(
                "policy attestation delete --attestation-name {rn}  --resource '{resource_id}'")

            # verify that the attestation has been deleted.
            self.cmd("policy attestation list  --resource '{resource_id}'", checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])
            # endregion

            # region Policy Attestation Resource CRUD Full

            self.kwargs.update({
                "assessment_date": "2023-01-01T08:29:18Z",
                'rn': self.create_random_name('azurecli-test-attestation', 40),
                "compliance_state": "Compliant",
                "evidence1": "source-uri=https://sampleuri.com description='Sample description for the sample uri'",
                "evidence2": "source-uri=https://sampleuri2.com description='Sample description 2 for the sample uri 2'",
                "expires_on": "2024-08-01T05:29:18Z",
                "owner": "user@microsoft.com",
                "metadata": "Location=NYC Dept=ACC"
            })

            assignment = self.cmd(
                'policy assignment show -n {initiative_id}').get_output_in_json()
            self.kwargs['pid'] = assignment['id'].lower()

            # create the attestation with all the properties
            self.cmd("policy attestation create --attestation-name {rn} --resource '{resource_id}' -a {initiative_id} --compliance-state {compliance_state} --assessment-date '{assessment_date}' --evidence {evidence1} --evidence {evidence2} --expires-on '{expires_on}' --owner {owner} --metadata {metadata} --definition-reference-id '{ref_id}'", checks=self._check_attestation_properties())

            # get the attestation at resource scope.
            self.cmd(
                'policy attestation show --attestation-name {rn}  --resource {resource_id}', checks=self._check_attestation_properties())

            # delete the attestation.
            self.cmd(
                'policy attestation delete --attestation-name {rn} --resource {resource_id}')

            # verify that the attestation has been deleted.
            self.cmd('policy attestation list --resource-id {resource_id}', checks=[
                self.check("length([?name == '{rn}'])", 0)
            ])
            # endregion
        finally:
            self._delete_all_attestations()

    def _test_policy_insights_attestation_collection(self):
        self.kwargs.update({
            'pan_resource': C.MANUAL_POLICY_RESOURCE_ASSIGNMENT,
            'rn_resource': self.create_random_name('azurecli-test-attestation', 40),
            'pan_sub': C.MANUAL_POLICY_SUB_ASSIGNMENT,
            'rn_sub': self.create_random_name('azurecli-test-attestation', 40),
            'pan_rg': C.MANUAL_POLICY_RG_INITIATIVE_ASSIGNMENT,
            'rn_rg': self.create_random_name('azurecli-test-attestation', 40),
            'resource_name': C.ATTESTATION_TEST_RESOURCE_NAME,
            'rg': C.ATTESTATION_TEST_RG_NAME,
            'ref_id': C.MANUAL_POLICY_RG_INITIATIVE_REFID,
            'sub': '086aecf4-23d6-4dfd-99a8-a5c6299f0322'
        })

        try:
            vnet = self.cmd(
                "network vnet show -n '{resource_name}' -g {rg}").get_output_in_json()
            self.kwargs['resource_id'] = vnet['id'].lower()

            # create a minimal attestation at resource scope
            self.cmd(
                "policy attestation create --attestation-name {rn_resource} -a {pan_resource} --resource '{resource_id}'")

            # create a minimal attestation at subscription scope
            self.cmd(
                'policy attestation create --attestation-name {rn_sub} -a {pan_sub}')

            # create a minimal attestation at resource group scope
            self.cmd(
                'policy attestation create --attestation-name {rn_rg} -g {rg} -a {pan_rg} --definition-reference-id {ref_id}')

            # region List Tests
            # list policy attestations at subscription scope
            self.cmd('az policy attestation list', checks=[
                self.check(
                    "length(@[?starts_with(name, 'azurecli-test-attestation')])", 3)
            ])

            # list at rg
            self.cmd('az policy attestation list -g {rg}', checks=[
                self.check(
                    "length(@[?starts_with(name, 'azurecli-test-attestation')])", 2)
            ])

            # # list at resource scope
            self.cmd('az policy attestation list --resource {resource_id}', checks=[
                self.check(
                    "length(@[?starts_with(name, 'azurecli-test-attestation')])", 1)
            ])

            # list with filter
            assignment = self.cmd(
                'policy assignment show -n {pan_rg}').get_output_in_json()
            self.kwargs['pid'] = self._replace_subscription_id(
                assignment['id'].lower(), self.kwargs['sub'])
            filter_clause = "PolicyAssignmentId eq '{pid}'"
            self.cmd('az policy attestation list --filter "{}"'.format(filter_clause), checks=[
                self.check(
                    "length(@[?starts_with(name, 'azurecli-test-attestation')])", 1)
            ])
            # list top 1 at resource group scope
            self.cmd('az policy attestation list -g {rg} --top 1', checks=[
                self.check(
                    "length(@[?starts_with(name, 'azurecli-test-attestation')])", 1)
            ])

            # endregion
        finally:
            self._delete_all_attestations()

    def _check_create_attestation_common(self):
        return [self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('resourceGroup',
                           '{rg}' if self.kwargs.get('rg') else None)
                ]

    def _check_attestation_properties(self):
        return [self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('policyDefinitionReferenceId',
                           '{ref_id}', case_sensitive=False),
                self.check('policyAssignmentId', '{pid}'),
                self.check('assessmentDate', '{assessment_date}'),
                self.check('complianceState', '{compliance_state}'),
                self.check('evidence[0].sourceUri', 'https://sampleuri.com'),
                self.check('evidence[0].description',
                           'Sample description for the sample uri'),
                self.check('evidence[1].sourceUri', 'https://sampleuri2.com'),
                self.check('evidence[1].description',
                           'Sample description 2 for the sample uri 2'),
                self.check('expiresOn', '{expires_on}'),
                self.check('owner', '{owner}'),
                self.check('metadata.Location', 'NYC'),
                self.check('metadata.Dept', 'ACC')]

    def _delete_all_attestations(self):
        all_attestations = self.cmd(
            'az policy attestation list').get_output_in_json()
        for attestation in all_attestations:
            resource_id = attestation['id'].replace(
                "{}/{}".format(C.ATTESTATION_RESOURCE_TYPE, attestation['name']), "")
            self.cmd('policy attestation delete --attestation-name "{}" --resource "{}"'.format(
                attestation['name'], resource_id))

    def _replace_subscription_id(self, resource_id, replacement_id):
        if resource_id:
            import re
            return re.sub("(subscriptions)/([^/]*)/",
                          r'\1/{}/'.format(replacement_id),
                          resource_id,
                          flags=re.IGNORECASE)
