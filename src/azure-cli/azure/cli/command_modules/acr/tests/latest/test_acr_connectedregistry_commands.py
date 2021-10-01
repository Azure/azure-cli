# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, StorageAccountPreparer, ResourceGroupPreparer, record_only


class AcrConnectedRegistryCommandsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_acr_connectedregistry(self, resource_group):
        # Agentpool prerequisites for connected registry testing
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'cr_name1': 'connectedRegistry1',
            'cr_name2': 'connectedRegistry2',
            'rg_loc': 'eastus',
            'sku': 'Premium',
            'syncToken': 'syncToken',
            'clientToken': 'clientToken',
            'clientToken2': 'clientToken2',
            'scopeMap': 'scopeMap1',
            'repo1': 'repo1',
            'repo2': 'repo2',
            'syncSchedule': '0 0/10 * * *',
            'defaultSyncSchedule': '* * * * *',
            'syncWindow': 'PT4H',
        })
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', '{sku}'),
                         self.check('sku.tier', '{sku}'),
                         self.check('provisioningState', 'Succeeded')])

        # Create a default connected registry.
        self.cmd('acr connected-registry create -n {cr_name1} -r {registry_name} --repository {repo1} {repo2}',
                 checks=[self.check('name', '{cr_name1}'),
                         self.check('mode', 'Registry'),
                         self.check('logging.logLevel', 'Information'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('resourceGroup', '{rg}')])

        # Create a custom connected-registry with a previously created token.
        self.cmd('acr token create -r {registry} -n {syncTtoken} --repository {repo1} content/read metadata/read --gateway {cr_name2} config/read config/write message/read message/write',
                 checks=self.check('credentials.passwords', []))
        self.cmd('acr token create -r {registry} -n {clientToken} --repository {repo1} content/read',
                 checks=self.check('credentials.passwords', []))
        self.cmd('acr connected-registry create -n {cr_name2} -r {registry_name} --sync-token {syncTtoken} -m mirror --log-level Warning -s "{syncSchedule}" -w {syncWindow} --client-tokens {clientToken}',
                 checks=[self.check('name', '{cr_name1}'),
                         self.check('mode', 'Mirror'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('logging.logLevel', 'Warning'),
                         self.check('parent.syncProperties.schedule', '{syncSchedule}'),
                         self.check('parent.syncProperties.syncWindow', '{syncWindow}'),
                         self.check('resourceGroup', '{rg}')])

        # List connected registries
        self.cmd('acr connected-registry list -r {registry_name}',
                 checks=[self.check('[0].name', '{cr_name2}'),
                         self.check('[1].name', '{cr_name1}')])

        # List client tokens
        self.cmd('acr connected-registry list-client-tokens -n {cr_name2} -r {registry_name}',
                 checks=[self.check('[0].name', '{clientToken}')])

        # Update the connected registry using
        self.cmd('acr token create -r {registry} -n {clientToken2} --repository {repo2} metadata/read',
                 checks=self.check('credentials.passwords', []))
        self.cmd('acr connected-registry update -n {cr_name2} -r {registry_name} --log-level Information -s "{defaultSyncSchedule}" --remove-client-tokens {clientToken} --add-client-tokens {clientToken2}',
                 checks=[self.check('name', '{cr_name1}'),
                         self.check('logging.logLevel', 'Information'),
                         self.check('parent.syncProperties.schedule', '{defaultSyncSchedule}'),
                         self.check('parent.syncProperties.syncWindow', 'None'),
                         self.check('resourceGroup', '{rg}')])

        # List client tokens
        self.cmd('acr connected-registry list-client-tokens -n {cr_name2} -r {registry_name}',
                 checks=[self.check('[0].name', '{clientToken2}')])

        # Delete connected registry 2
        self.cmd('acr connected-registry delete -n {cr_name2} -r {registry_name} -y')

        # show connected registry properties
        self.cmd('acr connected-registry show -n {cr_name1} -r {registry_name}',
                 checks=[self.check('name', '{cr_name1}')])

        # update connected registry repo permissions
        self.cmd('acr connected-registry repo -n {cr_name1} -r {registry_name} --remove {repo1} {repo2} --add foo')

        # Delete registry
        self.cmd('acr delete -n {registry_name} -g {rg} -y')
