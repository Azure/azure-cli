# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)


class NWFlowLogScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_nw_flow_log_', location='eastus')
    @StorageAccountPreparer(name_prefix='testflowlog', location='eastus', kind='StorageV2')
    def test_nw_flow_log_create(self, resource_group, resource_group_location, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'storage_account': storage_account,
            'nsg': 'nsg1',
            'watcher_rg': 'NetworkWatcherRG',
            'watcher_name': 'NetworkWatcher_{}'.format(resource_group_location),
            'flow_log': 'flow_log_test',
            'workspace': self.create_random_name('clitest', 20),
        })

        # enable network watcher
        # self.cmd('network watcher configure -g {rg} --locations {location} --enabled')

        # prepare the target resource
        self.cmd('network nsg create -g {rg} -n {nsg}')

        # prepare workspace
        workspace = self.cmd('monitor log-analytics workspace create '
                             '--resource-group {rg} '
                             '--location {location} '
                             '--workspace-name {workspace} ').get_output_in_json()
        self.kwargs.update({
            'workspace_id': workspace['id']
        })

        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--nsg {nsg} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        self.cmd('network watcher flow-log list --location {location}')

        # This output is Azure Management Resource formatted.
        self.cmd('network watcher flow-log show --location {location} --name {flow_log}', checks=[
            self.check('name', self.kwargs['flow_log']),
            self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.enabled', False),
            self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.workspaceResourceId',
                       self.kwargs['workspace_id']),
            self.check('retentionPolicy.days', 0),
            self.check('retentionPolicy.enabled', False),
        ])

    @ResourceGroupPreparer(name_prefix='test_nw_flow_log_', location='westus')
    @StorageAccountPreparer(name_prefix='testflowlog', location='westus', kind='StorageV2')
    def test_nw_flow_log_delete(self, resource_group, resource_group_location, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'storage_account': storage_account,
            'nsg': 'nsg1',
            'watcher_rg': 'NetworkWatcherRG',
            'watcher_name': 'NetworkWatcher_{}'.format(resource_group_location),
            'flow_log': 'flow_log_test2',
            'workspace': self.create_random_name('clitest', 20),
        })

        # enable network watcher
        # self.cmd('network watcher configure -g {rg} --locations {location} --enabled')

        # prepare the target resource
        self.cmd('network nsg create -g {rg} -n {nsg}')

        # prepare workspace
        workspace = self.cmd('monitor log-analytics workspace create '
                             '--resource-group {rg} '
                             '--location {location} '
                             '--workspace-name {workspace} ').get_output_in_json()
        self.kwargs.update({
            'workspace_id': workspace['id']
        })

        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--nsg {nsg} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        self.cmd('network watcher flow-log show --location {location} --name {flow_log}')

        self.cmd('network watcher flow-log delete --location {location} --name {flow_log}')

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('network watcher flow-log show --location {location} --name {flow_log}')

    @ResourceGroupPreparer(name_prefix='test_nw_flow_log_', location='westus')
    @StorageAccountPreparer(name_prefix='testflowlog', location='westus', kind='StorageV2')
    def test_nw_flow_log_show(self, resource_group, resource_group_location, storage_account):
        """
        This test is used to demonstrate different outputs between the new and deprecating parameters
        :param resource_group:
        :param resource_group_location:
        :param storage_account:
        :return:
        """
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'storage_account': storage_account,
            'nsg': 'nsg1',
            'watcher_rg': 'NetworkWatcherRG',
            'watcher_name': 'NetworkWatcher_{}'.format(resource_group_location),
            'flow_log': 'flow_log_test2',
            'workspace': self.create_random_name('clitest', 20),
        })

        # enable network watcher
        # self.cmd('network watcher configure -g {rg} --locations {location} --enabled')

        # prepare the target resource
        nsg_info = self.cmd('network nsg create -g {rg} -n {nsg}').get_output_in_json()
        self.kwargs.update({
            'nsg_id': nsg_info['NewNSG']['id']
        })

        # prepare workspace
        workspace = self.cmd('monitor log-analytics workspace create '
                             '--resource-group {rg} '
                             '--location {location} '
                             '--workspace-name {workspace} ').get_output_in_json()
        self.kwargs.update({
            'workspace_id': workspace['id']
        })

        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--nsg {nsg} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        # This output is new Azure Management Resource formatted.
        self.cmd('network watcher flow-log show --location {location} --name {flow_log}', checks=[
            self.check('name', self.kwargs['flow_log']),
            self.check('enabled', True),
            self.check('format.type', 'JSON'),
            self.check('format.version', 1),
            self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.enabled', False),
            self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.workspaceResourceId',
                       self.kwargs['workspace_id']),
            self.check('retentionPolicy.days', 0),
            self.check('retentionPolicy.enabled', False),
        ])

        # This output is deprecating
        self.cmd('network watcher flow-log show --nsg {nsg_id}', checks=[
            self.check('enabled', True),
            self.check('format.type', 'JSON'),
            self.check('format.version', 1),
            self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.enabled', False),
            self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.workspaceResourceId',
                       self.kwargs['workspace_id']),
            self.check('retentionPolicy.days', 0),
            self.check('retentionPolicy.enabled', False)
        ])

    @ResourceGroupPreparer(name_prefix='test_nw_flow_log_', location='eastus')
    @StorageAccountPreparer(name_prefix='testflowlog', location='eastus', kind='StorageV2')
    def test_nw_flow_log_update(self, resource_group, resource_group_location, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'storage_account': storage_account,
            'storage_account_2': 'storageaccount0395',
            'nsg': 'nsg1',
            'watcher_rg': 'NetworkWatcherRG',
            'watcher_name': 'NetworkWatcher_{}'.format(resource_group_location),
            'flow_log': 'flow_log_test2',
            'workspace': self.create_random_name('clitest', 20),
        })

        # enable network watcher
        # self.cmd('network watcher configure -g {rg} --locations {location} --enabled')

        # prepare the target resource
        nsg_info = self.cmd('network nsg create -g {rg} -n {nsg}').get_output_in_json()
        self.kwargs.update({
            'nsg_id': nsg_info['NewNSG']['id']
        })

        # prepare another storage account in another resource group
        storage_info = self.cmd('storage account create '
                                '--resource-group {rg} '
                                '--name {storage_account_2} --https-only').get_output_in_json()
        self.kwargs.update({
            'another_storage': storage_info['id']
        })

        # prepare workspace
        workspace = self.cmd('monitor log-analytics workspace create '
                             '--resource-group {rg} '
                             '--location {location} '
                             '--workspace-name {workspace} ').get_output_in_json()
        self.kwargs.update({
            'workspace_id': workspace['id']
        })

        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--nsg {nsg} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        res1 = self.cmd('network watcher flow-log show --location {location} --name {flow_log}').get_output_in_json()
        self.assertEqual(res1['name'], self.kwargs['flow_log'])
        self.assertEqual(res1['enabled'], True)
        self.assertEqual(res1['retentionPolicy']['days'], 0)
        self.assertEqual(res1['retentionPolicy']['enabled'], False)
        self.assertTrue(res1['storageId'].endswith(self.kwargs['storage_account']))
        self.assertIsNone(res1['tags'])

        res2 = self.cmd('network watcher flow-log update '
                        '--location {location} '
                        '--name {flow_log} '
                        '--retention 2 '
                        '--storage-account {another_storage} '
                        '--tags foo=bar ').get_output_in_json()
        self.assertEqual(res2['name'], self.kwargs['flow_log'])
        self.assertEqual(res2['enabled'], True)
        self.assertEqual(res2['retentionPolicy']['days'], 2)
        self.assertEqual(res2['retentionPolicy']['enabled'], True)
        self.assertTrue(res2['storageId'].endswith(self.kwargs['storage_account_2']))
        self.assertIsNotNone(res2['tags'])
