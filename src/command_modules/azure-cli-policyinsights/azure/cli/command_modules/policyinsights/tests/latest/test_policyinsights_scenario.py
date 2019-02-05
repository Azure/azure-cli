# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, create_random_name, record_only


class PolicyInsightsTests(ScenarioTest):

    @record_only()
    def test_policy_insights(self):
        top_clause = '--top 2'
        filter_clause = '--filter "isCompliant eq false"'
        apply_clause = '--apply "groupby((policyAssignmentId, resourceId), aggregate($count as numRecords))"'
        select_clause = '--select "policyAssignmentId, resourceId, numRecords"'
        order_by_clause = '--order-by "numRecords desc"'
        from_clause = '--from "2018-04-04T00:00:00"'
        to_clause = '--to "2018-05-22T00:00:00"'
        scopes = [
            '-m "azgovtest4"',
            '',
            '-g "defaultresourcegroup-eus"',
            '--resource "/subscriptions/00000000-0000-0000-0000-000000000000/resourcegroups/eastusnsggroup/providers/microsoft.network/networksecuritygroups/eastusnsg/securityrules/allow-joba"',
            '--resource "omssecuritydevkeyvalut" --namespace "microsoft.keyvault" --resource-type "vaults" -g "omssecurityintresourcegroup"',
            '--resource "default" --namespace "microsoft.network" --resource-type "subnets" --parent "virtualnetworks/mms-wcus-vnet" -g "mms-wcus"',
            '-s "335cefd2-ab16-430f-b364-974a170eb1d5"',
            '-d "25bf1e2a-6004-47ad-9bd1-2a40dd6de016"',
            '-a "96e22f7846e94bb186ae3a01"',
            '-a "bc916e4f3ab54030822a11b3" -g "tipkeyvaultresourcegroup" '
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
                self.check('deploymentStatus.totalDeployments', 0)
            ])

            self.cmd('policy remediation show -n {rn} -g {rg}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', '{rg}'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0)
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
                self.check('deploymentStatus.totalDeployments', 0)
            ])

            self.cmd('policy remediation show -n {rn}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', None),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters.locations[*] | length([])', 1),
                self.check('filters.locations[0]', '{location}'),
                self.check('deploymentStatus.totalDeployments', 0)
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
                self.check('deploymentStatus.totalDeployments', 0)
            ])

            self.cmd('policy remediation show -n {rn} -g {rg} --namespace "Microsoft.Storage" --resource-type storageAccounts --resource {sa}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', '{rg}'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0)
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
                self.check('deploymentStatus.totalDeployments', 0)
            ])

            self.cmd('policy remediation show -n {rn}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('resourceGroup', None),
                self.check('policyAssignmentId', '{pid}'),
                self.check('policyDefinitionReferenceId', '{drid}'),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0)
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
            'mg': self.create_random_name('cli-test-mg', 30),
            'bip': '06a78e20-9358-41c9-923c-fb736d382a4d'
        })

        # create a management group we can assign policy to
        management_group = self.cmd('account management-group create -n {mg}').get_output_in_json()

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
                self.check('deploymentStatus.totalDeployments', 0)
            ])

            self.cmd('policy remediation show -n {rn} -m {mg}', checks=[
                self.check('name', '{rn}'),
                self.check('provisioningState', 'Succeeded'),
                self.check('policyAssignmentId', '{pid}'),
                self.check('resourceGroup', None),
                self.check('policyDefinitionReferenceId', None),
                self.check('filters', None),
                self.check('deploymentStatus.totalDeployments', 0)
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
    @record_only()
    def test_policy_insights_remediation_complete(self):
        self.kwargs.update({
            'pan': 'eeb18edc813c42d0ad5a9eab',
            'rg': 'elpere',
            'rn': self.create_random_name('azurecli-test-remediation', 40)
        })

        assignment = self.cmd('policy assignment show -g {rg} -n {pan}').get_output_in_json()
        self.kwargs['pid'] = assignment['id'].lower()

        # create a remediation at resource group scope
        self.cmd('policy remediation create -n {rn} -g {rg} -a {pan}', checks=[
            self.check('name', '{rn}'),
            self.check('provisioningState', 'Accepted'),
            self.check('resourceGroup', '{rg}'),
            self.check('policyAssignmentId', '{pid}'),
            self.check('policyDefinitionReferenceId', None),
            self.check('filters', None),
            self.check('deploymentStatus.totalDeployments', 4)
        ])

        self.cmd('policy remediation show -n {rn} -g {rg}', checks=[
            self.check('name', '{rn}'),
            self.check('resourceGroup', '{rg}'),
            self.check('policyAssignmentId', '{pid}'),
            self.check('deploymentStatus.totalDeployments', 4)
        ])

        self.cmd('policy remediation list -g {rg}', checks=[
            self.check("length([?name == '{rn}'])", 1)
        ])

        self.cmd('policy remediation deployment list -n {rn} -g {rg}', checks=[
            self.check('length([])', 4),
            self.exists('[0].createdOn'),
            self.exists('[0].lastUpdatedOn'),
            self.exists('[0].resourceLocation'),
            self.exists('[0].status'),
            self.check("length([?contains(@.remediatedResourceId, '/resourcegroups/{rg}/providers/microsoft.compute/virtualmachines')])", 4)
        ])

        # cancel the remediation
        self.cmd('policy remediation cancel -n {rn} -g {rg}', checks=[
            self.check('provisioningState', 'Cancelling')
        ])
