# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, StorageAccountPreparer, ResourceGroupPreparer, record_only


class AcrConnectedRegistryCommandsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_acr_connectedregistry(self, resource_group):
        # Agentpool prerequisites for connected registry testing
        crName = 'connectedRegistry'
        rootName = 'rootregistry'
        childName = 'child'
        grandchildName = 'grandchild'
        repo1 = 'repo1'
        repo2 = 'repo2'
        repo3 = 'repo3'
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'cr_name': crName,
            'root_name': rootName,
            'child_name': childName,
            'grandchild_name': grandchildName,
            'rg_loc': 'eastus',
            'sku': 'Premium',
            'syncToken': 'syncToken',
            'clientToken': 'clientToken',
            'clientToken2': 'clientToken2',
            'scopeMap': 'scopeMap1',
            'repo_1': repo1,
            'repo_2': repo2,
            'repo_3': repo3,
            'syncSchedule': '0 0/10 * * *',
            'defaultSyncSchedule': '* * * * *',
            'syncWindow': 'PT4H',
            'notificationStr': 'hello-world:tag:push',
            'notificationStr2': '*:*'
        })
        # Create Registr and enable data endpoint
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', '{sku}'),
                         self.check('sku.tier', '{sku}'),
                         self.check('provisioningState', 'Succeeded')])
        self.cmd('acr update -n {registry_name} --data-endpoint-enabled true',
                 checks=self.check('dataEndpointEnabled', True))

        # Create a default connected registry.
        self.cmd('acr connected-registry create -n {cr_name} -r {registry_name} --repository {repo_1} {repo_2} {repo_3}',
                 checks=[self.check('name', '{cr_name}'),
                         self.check('mode', 'ReadWrite'),
                         self.check('logging.logLevel', 'Information'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('resourceGroup', '{rg}')])

        # Create a custom connected-registry with a previously created token.
        self.cmd('acr token create -r {registry_name} -n {syncToken} --repository {repo_1} content/read metadata/read --gateway {root_name} config/read config/write message/read message/write --no-passwords')
        self.cmd('acr token create -r {registry_name} -n {clientToken} --repository {repo_1} content/read --no-passwords')
        self.cmd('acr connected-registry create -n {root_name} -r {registry_name} --sync-token {syncToken} -m ReadOnly --log-level Warning -s "{syncSchedule}" -w PT4H --client-tokens {clientToken} --notifications {notificationStr}',
                 checks=[self.check('name', '{root_name}'),
                         self.check('mode', 'ReadOnly'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('logging.logLevel', 'Warning'),
                         self.check('parent.syncProperties.schedule', '{syncSchedule}'),
                         self.check('parent.syncProperties.syncWindow', '4:00:00'),
                         self.check('resourceGroup', '{rg}'),
                         self.check('notificationsList[0]', '{notificationStr}')])

        # Create Child connected registry
        self.cmd('acr connected-registry create -n {child_name} -p {root_name} -r {registry_name} --repository {repo_2} -m ReadOnly',
                 checks=[self.check('name', '{child_name}'),
                         self.check('mode', 'ReadOnly'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check("ends_with(parent.id, '{root_name}')", True),
                         self.check('resourceGroup', '{rg}')])

        # Create Grandchild connected registry
        self.cmd('acr connected-registry create -n {grandchild_name} -p {child_name} -r {registry_name} --repository {repo_2} -m ReadOnly',
                 checks=[self.check('name', '{grandchild_name}'),
                         self.check('mode', 'ReadOnly'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check("ends_with(parent.id, '{child_name}')", True),
                         self.check('resourceGroup', '{rg}')])

        # List connected registries
        self.cmd('acr connected-registry list -r {registry_name}',
                 checks=[self.check('[0].name', '{cr_name}'),
                         self.check('[1].name', '{root_name}')])

        # List client tokens
        self.cmd('acr connected-registry list-client-tokens -n {root_name} -r {registry_name}',
                 checks=[self.check('[0].name', '{clientToken}')])

        # Update the connected registry
        self.cmd('acr token create -r {registry_name} -n {clientToken2} --repository {repo_2} metadata/read --no-passwords')
        self.cmd('acr connected-registry update -n {root_name} -r {registry_name} --log-level Information -s "{defaultSyncSchedule}" --remove-client-tokens {clientToken} --add-client-tokens {clientToken2} --add-notifications {notificationStr2} --remove-notifications {notificationStr}',
                 checks=[self.check('name', '{root_name}'),
                         self.check('logging.logLevel', 'Information'),
                         self.check('parent.syncProperties.schedule', '{defaultSyncSchedule}'),
                         self.check('parent.syncProperties.syncWindow', 'None'),
                         self.check('resourceGroup', '{rg}'),
                         self.check('notificationsList[0]', '{notificationStr2}')])

        # List client tokens
        self.cmd('acr connected-registry list-client-tokens -n {root_name} -r {registry_name}',
                 checks=[self.check('[0].name', '{clientToken2}')])

        # Show connected registry properties
        self.cmd('acr connected-registry show -n {cr_name} -r {registry_name}',
                 checks=[self.check('name', '{cr_name}')])

        # Get connection string a generate new password.
        self.cmd('acr connected-registry get-settings -n {root_name} -r {registry_name} --parent-protocol https --generate-password 2 -y')
        self.cmd('acr token show -n {syncToken} -r {registry_name}', checks=[
            self.check('credentials.passwords[0].name', 'password2')])

        # Update and check connected registry repo permissions
        self.cmd('acr connected-registry permissions update -n {grandchild_name} -r {registry_name} --add {repo_1} {repo_3}')

        scope_map = self.cmd('acr connected-registry permissions show -n {root_name} -r {registry_name}').get_output_in_json()
        self.assertListEqual(sorted(scope_map['actions']),
                             ['gateway/'+ childName +'/config/read', 'gateway/'+ childName +'/config/write',
                              'gateway/'+ childName +'/message/read', 'gateway/'+ childName +'/message/write',
                              'gateway/'+ grandchildName +'/config/read', 'gateway/'+ grandchildName +'/config/write',
                              'gateway/'+ grandchildName +'/message/read', 'gateway/'+ grandchildName +'/message/write',
                              'gateway/'+ rootName +'/config/read', 'gateway/'+ rootName +'/config/write',
                              'gateway/'+ rootName +'/message/read', 'gateway/'+ rootName +'/message/write',
                              'repositories/'+ repo1 +'/content/read', 'repositories/'+ repo1 +'/metadata/read',
                              'repositories/'+ repo2 +'/content/read', 'repositories/'+ repo2 +'/metadata/read',
                              'repositories/'+ repo3 +'/content/read', 'repositories/'+ repo3 +'/metadata/read'])

        self.cmd('acr connected-registry permissions update -n {root_name} -r {registry_name} --remove {repo_1} {repo_2}')
        self.cmd('acr connected-registry permissions update -n {child_name} -r {registry_name} --remove {repo_3} --add {repo_1}')

        scope_map = self.cmd('acr connected-registry permissions show -n {grandchild_name} -r {registry_name}').get_output_in_json()
        self.assertListEqual(sorted(scope_map['actions']),
                             ['gateway/'+ grandchildName +'/config/read', 'gateway/'+ grandchildName +'/config/write',
                              'gateway/'+ grandchildName +'/message/read', 'gateway/'+ grandchildName +'/message/write'])

        # Delete connected registry grand child
        self.cmd('acr connected-registry delete -n {grandchild_name} -r {registry_name} --cleanup -y')

        # Check Gateway permission is removed by cleanup
        scope_map = self.cmd('acr connected-registry permissions show -n {child_name} -r {registry_name}').get_output_in_json()
        self.assertListEqual(sorted(scope_map['actions']),
                             ['gateway/'+ childName +'/config/read', 'gateway/'+ childName +'/config/write',
                              'gateway/'+ childName +'/message/read', 'gateway/'+ childName +'/message/write',
                              'repositories/'+ repo1 +'/content/read', 'repositories/'+ repo1 +'/metadata/read'])

        # Delete connected registry child
        self.cmd('acr connected-registry delete -n {child_name} -r {registry_name} -y')

        # Delete registry
        self.cmd('acr delete -n {registry_name} -g {rg} -y')
