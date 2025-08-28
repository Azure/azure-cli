# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, create_random_name, live_only, record_only
from azure.cli.testsdk.exceptions import JMESPathCheckAssertionError
from .test_utils import AttestationConstants as C

# ----------------------------------------------
# 2025/6/18 (cstack):
# ----------------------------------------------
# - Test suite mostly rerecorded as part of Azure Policy CRUD command migration to auto-generation.
# - Rewrote two tests that required manual setup to record, now do their own setup and teardown:
#     test_policy_insights_remediation_complete()
#     test_policy_insights_attestation()
# - Fixed a few bugs in tests that only show up during recording.
# - $$$ Attestation tests are temporarily hacked to bits to work around a service bug. Currently resource-level
#   attestations cannot be deleted, so the logic of the test is completely broken. Comments with $$$ tag the
#   areas that had to be modified or commented out in order to make progress. Once the service bug is fixed,
#   we will circle back to restore the resource-level attestation tests.
#
# All tests now do their own setup and teardown (and were rerecorded) except test_policy_insights()
# which still depends on complex manual setup prior to recording. Not coincidentally, it has not been
# re-recorded since original check-in 2/1/2023. This test still needs to be fixed to create its own resources.
# ----------------------------------------------
class PolicyInsightsTests(ScenarioTest):

    # Current recording was recorded against "Azure Governance Perf 24" (3593b919-b078-4cc1-902f-201232a97ac0)
    # 2025/6/18 (cstack) - Did not need to rerecord this one.
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
    @StorageAccountPreparer(name_prefix='cliremediation', allow_shared_key_access=False)
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
    def test_policy_insights_remediation_management_group(self):
        self.kwargs.update({
            'pan': self.create_random_name('cli-test-pa', 23),
            'rn': self.create_random_name('cli-test-remediation', 30),
            'mg': 'PowershellTesting',
            'bip': '06a78e20-9358-41c9-923c-fb736d382a4d'
        })

        try:
            # create a policy assignment that we can trigger remediations on
            self.kwargs['mgid'] = '/providers/Microsoft.Management/managementGroups/PowershellTesting'
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

    # Executing a real remediation requires time-intensive setup. These setup steps are performed by this test
    # prior to executing a real remediation against a known non-compliant policy.
    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(name_prefix='cli_test_remediation')
    @StorageAccountPreparer(
        name_prefix='cliremediation1',
        location='westus2',
        key='stor1',
        sku='Standard_RAGRS',
        kind='StorageV2',
        allow_shared_key_access=False)
    @StorageAccountPreparer(
        name_prefix='cliremediation2',
        location='southcentralus',
        key='stor2',
        sku='Standard_RAGRS',
        kind='StorageV2',
        allow_shared_key_access=False)
    def test_policy_insights_remediation_complete(self):
        self.kwargs.update({
            'pan': self.create_random_name('clitestrgassignment', 30),
            'rn': self.create_random_name('azurecli-test-remediation', 40),
            'pan_sub': self.create_random_name('clitestsubassignment', 30),
            'location1': 'westus2',
            'location2': 'southcentralus',
            'pdn': '361c2074-3595-4e5d-8cab-4f21dffc835c',
            'pddn': 'CLI test assignment for policy insights remediation.'
        })

        try:
            # create assignments at the RG level and subscription level
            self.cmd('policy assignment create -n {pan} -g {rg} --policy {pdn} -l {location1} --system-assigned --display-name "{pddn}"')
            self.cmd('policy assignment create -n {pan_sub} --policy {pdn} -l {location2} --system-assigned --display-name "{pddn}"')

            # trigger policy scan (this takes minutes)
            self.cmd('policy state trigger-scan -g {rg}')

            # get the id for the resource group scope assignment
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

            # get the id of the subscription scope assignment
            assignment = self.cmd(
                'policy assignment show -n {pan_sub}').get_output_in_json()

            self.kwargs['pid'] = assignment['id'].lower()
            self.kwargs['rn'] = self.create_random_name('azurecli-test-remediation', 40)

            # create a remediation at subscription scope with full id of policy assignment
            self.cmd('policy remediation create -n {rn} -a {pid}', checks=[
                self.check('name', '{rn}'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('resourceDiscoveryMode', 'ExistingNonCompliant')
            ])

            # cancel the remediation created above
            self.cmd('policy remediation cancel -n {rn}', checks=[
                self.check('provisioningState', 'Cancelling')
            ])

        finally:
            self.cmd('policy assignment delete -n {pan} -g {rg}')
            self.cmd('policy assignment delete -n {pan_sub}')

    # Test a remediation that re-evaluates compliance results before remediating
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_remediation')
    @StorageAccountPreparer(name_prefix='cliremediation', allow_shared_key_access=False)
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
    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_remediation')
    def test_policy_insights_attestation(self):
        self.kwargs.update({
            'pdn1': self.create_random_name('clitestdefinition', 30),
            'pdn2': self.create_random_name('clitestdefinition', 30),
            'pdn3': self.create_random_name('clitestdefinition', 30),
            'pin1': self.create_random_name('clitestinitiative', 30),
            'pin2': self.create_random_name('clitestinitiative', 30),
            'pin3': self.create_random_name('clitestinitiative', 30),
            'pddn': 'CLI test artifact for policy insights attestation.',
            'pan_resource': self.create_random_name('clitestassignment', 30),
            'pan_rg': self.create_random_name('clitestassignment', 30),
            'pan_sub': self.create_random_name('clitestassignment', 30),
            'pain_resource': self.create_random_name('clitestassignment', 30),
            'pain_rg': self.create_random_name('clitestassignment', 30),
            'pain_sub': self.create_random_name('clitestassignment', 30),
            'ref_id': 'clitest',
            'resource_name': self.create_random_name('clitestresource', 30),
            'sub': self.get_subscription_id(),
            'assessment_date': '2023-01-01T08:29:18Z',
            "compliance_state": "Compliant",
            "evidence1": "source-uri=https://sampleuri.com description='Sample description for the sample uri'",
            "evidence2": "source-uri=https://sampleuri2.com description='Sample description 2 for the sample uri 2'",
            "expires_on": "2024-08-01T05:29:18Z",
            "owner": "test@example.com",        # must be this value to work with test framework record file hackery
            "metadata": "Location=NYC Dept=ACC"
        })

        try:
            # $$$ Temporarily keep a list of attestations created in this test to delete them later
            self.attestations_created = []

            # get the resource group location
            resource_group = self.cmd('group show -n {rg}').get_output_in_json()
            self.kwargs['location'] = resource_group['location']

            # create a resource and get its id
            self.cmd('network vnet create -n {resource_name} -g {rg}')
            vnet = self.cmd(
                "network vnet show -n '{resource_name}' -g {rg}").get_output_in_json()
            self.kwargs['resource_id'] = vnet['id'].lower()

            # create a manual policy definition for resource level and get its id
            self.cmd('policy definition create -n {pdn1} --rule "{{\\"if\\":{{\\"allOf\\":[{{\\"field\\":\\"type\\",\\"equals\\":\\"Microsoft.Network/virtualNetworks\\"}},{{\\"field\\":\\"Microsoft.Network/virtualNetworks/privateEndpointVNetPolicies\\",\\"equals\\":\\"Disabled\\"}}]}},\\"then\\":{{\\"effect\\":\\"manual\\"}}}}" --display-name "{pddn}" --mode All')
            definition = self.cmd(
                'policy definition show -n {pdn1}').get_output_in_json()
            self.kwargs['def_id'] = definition['id'].lower()

            # create a policy set for the manual policy
            self.cmd('policy set-definition create -n {pin1} --definitions "[{{\\"policyDefinitionReferenceId\\":\\"{ref_id}\\",\\"policyDefinitionId\\":\\"{def_id}\\" }}]" --display-name "{pddn}"')

            # create a resource level policy assignment and get its id
            self.cmd('policy assignment create -n {pan_resource} --scope {resource_id} --policy {pdn1} -l {location} --display-name "{pddn}"')
            assignment = self.cmd(
                'policy assignment show -n {pan_resource} --scope {resource_id}').get_output_in_json()
            self.kwargs['presource_id'] = assignment['id'].lower()

            # create a resource level initiative assignment and get its id
            self.cmd('policy assignment create -n {pain_resource} --scope {resource_id} -d {pin1} -l {location} --display-name "{pddn}"')
            assignment = self.cmd(
                'policy assignment show -n {pain_resource} --scope {resource_id}').get_output_in_json()
            self.kwargs['piresource_id'] = assignment['id'].lower()

            # create a manual policy definition for resource group level and get its id
            self.cmd('policy definition create -n {pdn2} --rule "{{\\"if\\":{{\\"field\\":\\"type\\",\\"equals\\":\\"Microsoft.Resources/subscriptions/resourceGroups\\"}},\\"then\\":{{\\"effect\\":\\"manual\\"}}}}" --display-name "{pddn}" --mode All')
            definition = self.cmd(
                'policy definition show -n {pdn2}').get_output_in_json()
            self.kwargs['def_id'] = definition['id'].lower()

            # create a policy set for the manual policy
            self.cmd('policy set-definition create -n {pin2} --definitions "[{{\\"policyDefinitionReferenceId\\":\\"{ref_id}\\",\\"policyDefinitionId\\":\\"{def_id}\\" }}]" --display-name "{pddn}"')

            # create a resource group level policy assignment and get its id
            self.cmd('policy assignment create -n {pan_rg} -g {rg} --policy {pdn2} -l {location} --display-name "{pddn}"')
            assignment = self.cmd(
                'policy assignment show -n {pan_rg} -g {rg}').get_output_in_json()
            self.kwargs['prg_id'] = assignment['id'].lower()

            # create a resource group level initiative assignment and get its id
            self.cmd('policy assignment create -n {pain_rg} -g {rg} -d {pin2} -l {location} --display-name "{pddn}"')
            assignment = self.cmd(
                'policy assignment show -n {pain_rg} -g {rg}').get_output_in_json()
            self.kwargs['pirg_id'] = assignment['id'].lower()

            # create a manual policy definition for subscription level and get its id
            self.cmd('policy definition create -n {pdn3} --rule "{{\\"if\\":{{\\"field\\":\\"type\\",\\"equals\\":\\"Microsoft.Resources/subscriptions\\"}},\\"then\\":{{\\"effect\\":\\"manual\\"}}}}" --display-name "{pddn}" --mode All')
            definition = self.cmd(
                'policy definition show -n {pdn3}').get_output_in_json()
            self.kwargs['def_id'] = definition['id'].lower()

            # create a policy set for the manual policy
            self.cmd('policy set-definition create -n {pin3} --definitions "[{{\\"policyDefinitionReferenceId\\":\\"{ref_id}\\",\\"policyDefinitionId\\":\\"{def_id}\\" }}]" --display-name "{pddn}"')

            # create a subscription level policy assignment and get its id
            self.cmd('policy assignment create -n {pan_sub} --policy {pdn3} -l {location} --display-name "{pddn}"')
            assignment = self.cmd(
                'policy assignment show -n {pan_sub}').get_output_in_json()
            self.kwargs['psub_id'] = assignment['id'].lower()

            # create a subscription level initiative assignment and get its id
            self.cmd('policy assignment create -n {pain_sub} -d {pin3} -l {location} --display-name "{pddn}"')
            assignment = self.cmd(
                'policy assignment show -n {pain_sub}').get_output_in_json()
            self.kwargs['pisub_id'] = assignment['id'].lower()

            # trigger compliance scans for the subscription and resource group
            self.cmd('policy state trigger-scan')
            self.cmd('policy state trigger-scan -g {rg}')

            self._test_policy_insights_attestation_sub()
            # $$$ Temporarily disable tests of resource-level attestations pending a fix to the leaked attestation service bug
            #self._test_policy_insights_attestation_resource()
            self._test_policy_insights_attestation_rg()
            self._test_policy_insights_attestation_collection()
        finally:
            self._delete_all_attestations()
            self.cmd('policy assignment delete -n {pan_resource} --scope {resource_id}')
            self.cmd('policy assignment delete -n {pan_rg} -g {rg}')
            self.cmd('policy assignment delete -n {pan_sub}')
            self.cmd('policy assignment delete -n {pain_resource} --scope {resource_id}')
            self.cmd('policy assignment delete -n {pain_rg} -g {rg}')
            self.cmd('policy assignment delete -n {pain_sub}')
            self.cmd('policy set-definition delete -n {pin1} -y')
            self.cmd('policy set-definition delete -n {pin2} -y')
            self.cmd('policy set-definition delete -n {pin3} -y')
            self.cmd('policy definition delete -n {pdn1} -y')
            self.cmd('policy definition delete -n {pdn2} -y')
            self.cmd('policy definition delete -n {pdn3} -y')
            self.cmd('network vnet delete -n {resource_name} -g {rg}')

    def _test_policy_insights_attestation_rg(self):
        self.kwargs.update({
            'rn': self.create_random_name('azurecli-test-attestation', 40)
        })

        # region Policy Attestation RG CRUD minimal
        # create a minimal attestation at resource group scope
        self.cmd(
            'policy attestation create --attestation-name {rn} -g {rg} -a {pan_rg}', checks=self._check_create_attestation_common('prg_id', 'rg'))

        # get the attestation at resource group scope
        att = self.cmd(
            'policy attestation show --attestation-name {rn} -g {rg}', checks=self._check_create_attestation_common('prg_id', 'rg')
        ).get_output_in_json()

        # $$$ Temporarily save the id of the newly created attestation
        self.attestations_created.append(att)

        # update the attestation at resource group scope
        self.kwargs['comments'] = 'Adding a comment'
        self.cmd("policy attestation update --attestation-name {rn} -g {rg} --comments '{comments}'", checks=[
                    self.check('comments', '{comments}')] + self._check_create_attestation_common('prg_id', 'rg'))

        # delete an attestation at resource group scope
        self.cmd(
            'policy attestation delete --attestation-name {rn} -g {rg}')

        self.cmd('policy attestation list -g {rg}', checks=[
            self.check("length([?name == '{rn}'])", 0)
        ])
        # endregion

        # region Policy Attestation RG CRUD Full
        # create an attestation with all the properties at RG scope.
        self.cmd(
            "policy attestation create --attestation-name {rn} -g {rg} -a {pain_rg} --compliance-state {compliance_state} --assessment-date '{assessment_date}' --evidence {evidence1} --evidence {evidence2} --expires-on '{expires_on}' --owner {owner} --metadata {metadata} --definition-reference-id '{ref_id}' --debug", checks=self._check_attestation_properties('pirg_id'))

        # get the attestation at resource group scope
        att = self.cmd(
            'policy attestation show --attestation-name {rn} -g {rg}', checks=self._check_attestation_properties('pirg_id')
        ).get_output_in_json()

        # $$$ Temporarily save the id of the newly created attestation
        self.attestations_created.append(att)

        self.cmd(
            'policy attestation delete --attestation-name {rn} -g {rg}')

        self.cmd('policy attestation list -g {rg}', checks=[
            self.check("length([?name == '{rn}'])", 0)
        ])
        # endregion

    def _test_policy_insights_attestation_sub(self):
        self.kwargs.update({
            #'pan': self.create_random_name('clitestassignment', 30),
            'rn': self.create_random_name('azurecli-test-attestation', 40)
            #'initiative_id': C.MANUAL_POLICY_SUB_INITIATIVE_ASSIGNMENT,
            #'ref_id': C.MANUAL_POLICY_SUB_INITIATIVE_REFID
        })

        # region Policy Attestation Subscription CRUD minimal
        # create a minimal attestation at subscription scope
        self.cmd(
            'policy attestation create --attestation-name {rn} -a {pan_sub}', checks=self._check_create_attestation_common('psub_id'))

        # get the attestation at subscription scope
        att = self.cmd(
            'policy attestation show --attestation-name {rn}', checks=self._check_create_attestation_common('psub_id')
        ).get_output_in_json()

        # $$$ Temporarily save the id of the newly created attestation
        self.attestations_created.append(att)

        # update the attestation at subscription scope
        self.kwargs['comments'] = 'Adding a comment'
        self.cmd("policy attestation update --attestation-name {rn} --comments '{comments}'", checks=[
                    self.check('comments', '{comments}')] + self._check_create_attestation_common('psub_id'))

        # delete an attestation at subscription scope
        self.cmd('policy attestation delete --attestation-name {rn}')

        # verify that the attestation has been deleted.
        self.cmd('policy attestation list', checks=[
            self.check("length([?name == '{rn}'])", 0)
        ])
        # endregion

        # region Policy Attestation Subscription CRUD Full
        self.kwargs.update({
            'rn': self.create_random_name('azurecli-test-attestation', 40)
        })

        att = self.cmd(
            "policy attestation create --attestation-name {rn} -a {pain_sub} --compliance-state {compliance_state} --assessment-date '{assessment_date}' --evidence {evidence1} --evidence {evidence2} --expires-on '{expires_on}' --owner {owner} --metadata {metadata} --definition-reference-id '{ref_id}'", checks=self._check_attestation_properties('pisub_id')
        ).get_output_in_json()

        # $$$ Temporarily save the id of the newly created attestation
        self.attestations_created.append(att)

        # get the attestation at subscription scope
        self.cmd(
            'policy attestation show --attestation-name {rn}', checks=self._check_attestation_properties('pisub_id'))

        # delete the attestation.
        self.cmd('policy attestation delete --attestation-name {rn}')

        # verify that the attestation has been deleted.
        self.cmd('policy attestation list', checks=[
            self.check("length([?name == '{rn}'])", 0)
        ])
        # endregion

    def _test_policy_insights_attestation_resource(self):
        self.kwargs.update({
            'rn': self.create_random_name('azurecli-test-badattestation', 40),
        })

        # region Policy Attestation Resource CRUD minimal
        # create a minimal attestation at resource scope
        self.cmd(
            "policy attestation create --attestation-name {rn} -a {pan_resource} --resource '{resource_id}'", checks=self._check_create_attestation_common('presource_id', 'rg'))

        # get the attestation at resource scope
        self.cmd("policy attestation show --attestation-name {rn} --resource '{resource_id}'", checks=[
            self.check('name', '{rn}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('policyDefinitionReferenceId', None),
            self.check('policyAssignmentId', '{presource_id}')
        ])

        # update the attestation at resource scope
        self.kwargs['comments'] = 'Adding a comment'
        self.cmd("policy attestation update --attestation-name {rn} --comments '{comments}' --resource '{resource_id}'", checks=[
                    self.check('comments', '{comments}')] + self._check_create_attestation_common('presource_id', 'rg'))

        # delete an attestation at resource scope
        self.cmd(
            "policy attestation delete --attestation-name {rn} --resource '{resource_id}'")

        # verify that the attestation has been deleted (currently not working).
        self.cmd("policy attestation list  --resource '{resource_id}'", checks=[
            self.check("length([?name == '{rn}'])", 1)     # change this 1 to 0 after resource level deletion is working
        ])
        # endregion

        # region Policy Attestation Resource CRUD Full
        self.kwargs.update({
            'rn': self.create_random_name('azurecli-test-badattestation', 40)
        })

        # create the attestation with all the properties
        self.cmd("policy attestation create --attestation-name {rn} --resource '{resource_id}' -a {pain_resource} --compliance-state {compliance_state} --assessment-date '{assessment_date}' --evidence {evidence1} --evidence {evidence2} --expires-on '{expires_on}' --owner {owner} --metadata {metadata} --definition-reference-id '{ref_id}'", checks=self._check_attestation_properties('piresource_id'))

        # get the attestation at resource scope.
        self.cmd(
            'policy attestation show --attestation-name {rn}  --resource {resource_id}', checks=self._check_attestation_properties('piresource_id'))

        # delete the attestation.
        self.cmd(
            'policy attestation delete --attestation-name {rn} --resource {resource_id}')

        # verify that the attestation has been deleted (currently not working).
        self.cmd('policy attestation list --resource-id {resource_id}', checks=[
            self.check("length([?name == '{rn}'])", 1)     # change this 1 to 0 after resource level deletion is working
        ])
        # endregion

    def _test_policy_insights_attestation_collection(self):
        self.kwargs.update({
            'rn_resource': self.create_random_name('azurecli-test-attestation', 40),
            'rn_sub': self.create_random_name('azurecli-test-attestation', 40),
            'rn_rg': self.create_random_name('azurecli-test-attestation', 40)
        })

        # create a minimal initiative attestation at resource scope
        self.cmd(
            "policy attestation create --attestation-name {rn_resource} -a {pain_resource} --resource '{resource_id}'")

        # create a minimal initiative attestation at subscription scope
        att = self.cmd(
            'policy attestation create --attestation-name {rn_sub} -a {pain_sub}'
        ).get_output_in_json()

        # $$$ Temporarily save the id of the newly created attestation
        self.attestations_created.append(att)

        # create a minimal initiative attestation at resource group scope
        att = self.cmd(
            'policy attestation create --attestation-name {rn_rg} -g {rg} -a {pain_rg} --definition-reference-id {ref_id}'
        ).get_output_in_json()

        # $$$ Temporarily save the id of the newly created attestation
        self.attestations_created.append(att)

        # region List Tests
        # list policy attestations at subscription scope
        # $$$ Temporarily disable this check since it is not working with the attestation leak service bug
        # self.cmd('az policy attestation list', checks=[
        #     self.check(
        #         "length(@[?starts_with(name, 'azurecli-test-attestation')])", 3)
        # ])

        # list at rg
        self.cmd('az policy attestation list -g {rg}', checks=[
            self.check(
                "length(@[?starts_with(name, 'azurecli-test-attestation')])", 2)
        ])

        # list at resource scope
        # $$$ Temporarily disable this check since it is not working with the attestation leak service bug
        # self.cmd('az policy attestation list --resource {piresource_id}', checks=[
        #     self.check(
        #         "length(@[?starts_with(name, 'azurecli-test-attestation')])", 1)
        # ])

        # list with filter
        filter_clause = "PolicyAssignmentId eq '{}'".format(self.kwargs['pisub_id'])
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

    def _check_create_attestation_common(self, pid_key, rg_key=None):
        return [self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('policyAssignmentId', self.kwargs[pid_key]),
                self.check('resourceGroup', self.kwargs[rg_key] if rg_key else None)
                ]

    def _check_attestation_properties(self, pid_key):
        return [self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('policyDefinitionReferenceId',
                           '{ref_id}', case_sensitive=False),
                self.check('policyAssignmentId', self.kwargs[pid_key]),
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
        # $$$ Temporarily only delete explicit IDs to workaround attestation leak service bug
        # all_attestations = self.cmd(
        #     'az policy attestation list').get_output_in_json()
        all_attestations = self.attestations_created
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
