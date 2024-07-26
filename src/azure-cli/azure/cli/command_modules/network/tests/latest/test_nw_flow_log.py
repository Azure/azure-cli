# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)
from azure.cli.testsdk.scenario_tests.decorators import AllowLargeResponse


class NWFlowLogScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_nw_flow_log_', location='centraluseuap')
    @StorageAccountPreparer(name_prefix='testflowlog', location='centraluseuap', kind='StorageV2')
    def test_nw_flow_log_create_vnetfl(self, resource_group, resource_group_location, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'storage_account': storage_account,
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'nic': 'nic1',
            'watcher_rg': 'NetworkWatcherRG',
            'watcher_name': 'NetworkWatcher_{}'.format(resource_group_location),
            'flow_log': 'flow_log_test',
            'workspace': self.create_random_name('clitest', 20),
        })

        # enable network watcher
        # self.cmd('network watcher configure -g {rg} --locations {location} --enabled')

        # prepare the target resource
        self.cmd('network vnet create -g {rg} -n {vnet}')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet} --address-prefix 10.0.0.0/24')
        self.cmd('network nic create -g {rg} -n {nic} --vnet-name {vnet} --subnet {subnet}')

        # prepare workspace
        workspace = self.cmd('monitor log-analytics workspace create '
                             '--resource-group {rg} '
                             '--location eastus '
                             '--workspace-name {workspace} ').get_output_in_json()
        self.kwargs.update({
            'workspace_id': workspace['id']
        })

        #targetId as vnet
        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--vnet {vnet} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        self.cmd('network watcher flow-log list --location {location}')

        # This output is Azure Management Resource formatted.
        self.cmd('network watcher flow-log show --location {location} --name {flow_log}', checks=[
            self.check('name', self.kwargs['flow_log']),
            self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.workspaceResourceId',
                       self.kwargs['workspace_id']),
            self.check_pattern('targetResourceId', '.*/{vnet}$'),
            self.check('retentionPolicy.days', 0),
            self.check('retentionPolicy.enabled', False),
        ])

        #targetId as subnet
        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--vnet {vnet} '
                 '--subnet {subnet} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        self.cmd('network watcher flow-log list --location {location}')

        # This output is Azure Management Resource formatted.
        self.cmd('network watcher flow-log show --location {location} --name {flow_log}', checks=[
            self.check('name', self.kwargs['flow_log']),
            self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.workspaceResourceId',
                       self.kwargs['workspace_id']),
            self.check_pattern('targetResourceId', '.*/{subnet}$'),
            self.check('retentionPolicy.days', 0),
            self.check('retentionPolicy.enabled', False),
        ])
        
        #targetId as nic
        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--nic {nic} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        self.cmd('network watcher flow-log list --location {location}')

        # This output is Azure Management Resource formatted.
        self.cmd('network watcher flow-log show --location {location} --name {flow_log}', checks=[
            self.check('name', self.kwargs['flow_log']),
            self.check('flowAnalyticsConfiguration.networkWatcherFlowAnalyticsConfiguration.workspaceResourceId',
                       self.kwargs['workspace_id']),
            self.check_pattern('targetResourceId', '.*/{nic}$'),
            self.check('retentionPolicy.days', 0),
            self.check('retentionPolicy.enabled', False),
        ])

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
    
    @ResourceGroupPreparer(name_prefix='test_nw_flow_log_', location='centraluseuap')
    @StorageAccountPreparer(name_prefix='testflowlog', location='centraluseuap', kind='StorageV2')
    @AllowLargeResponse(1024)
    def test_nw_flow_log_delete_vnetfl(self, resource_group, resource_group_location, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'storage_account': storage_account,
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'nic': 'nic1',
            'watcher_rg': 'NetworkWatcherRG',
            'watcher_name': 'NetworkWatcher_{}'.format(resource_group_location),
            'flow_log': 'flow_log_test2',
            'workspace': self.create_random_name('clitest', 20),
        })

        # enable network watcher
        # self.cmd('network watcher configure -g {rg} --locations {location} --enabled')

        # prepare the target resource
        self.cmd('network vnet create -g {rg} -n {vnet}')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet} --address-prefix 10.0.0.0/24')
        self.cmd('network nic create -g {rg} -n {nic} --vnet-name {vnet} --subnet {subnet}')

        # prepare workspace
        workspace = self.cmd('monitor log-analytics workspace create '
                             '--resource-group {rg} '
                             '--location westus '
                             '--workspace-name {workspace} ').get_output_in_json()
        self.kwargs.update({
            'workspace_id': workspace['id']
        })

        #targetId as vnet
        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--vnet {vnet} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        self.cmd('network watcher flow-log show --location {location} --name {flow_log}')

        self.cmd('network watcher flow-log delete --location {location} --name {flow_log}')

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('network watcher flow-log show --location {location} --name {flow_log}')
        
        #targetId as subnet
        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--vnet {vnet} '
                 '--subnet {subnet} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        self.cmd('network watcher flow-log show --location {location} --name {flow_log}')

        self.cmd('network watcher flow-log delete --location {location} --name {flow_log}')

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('network watcher flow-log show --location {location} --name {flow_log}')

        
        #targetId as nic
        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--nic {nic} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        self.cmd('network watcher flow-log show --location {location} --name {flow_log}')

        self.cmd('network watcher flow-log delete --location {location} --name {flow_log}')

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('network watcher flow-log show --location {location} --name {flow_log}')
        
    @ResourceGroupPreparer(name_prefix='test_nw_flow_log_', location='eastus')
    @StorageAccountPreparer(name_prefix='testflowlog', location='eastus', kind='StorageV2')
    @AllowLargeResponse(1024)
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
    @AllowLargeResponse(1024)
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

    @ResourceGroupPreparer(name_prefix='test_nw_flow_log_', location='centraluseuap')
    @StorageAccountPreparer(name_prefix='testflowlog', location='centraluseuap', kind='StorageV2')
    def test_nw_flow_log_update_vnetfl(self, resource_group, resource_group_location, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            'location': resource_group_location,
            'storage_account': storage_account,
            'nsg': 'nsg1',
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'nic': 'nic1',
            'watcher_rg': 'NetworkWatcherRG',
            'watcher_name': 'NetworkWatcher_{}'.format(resource_group_location),
            'flow_log': 'flow_log_test2',
            'workspace': self.create_random_name('clitest', 20),
        })

        # enable network watcher
        # self.cmd('network watcher configure -g {rg} --locations {location} --enabled')

        # prepare the target resource
        self.cmd('network nsg create -g {rg} -n {nsg}')
        self.cmd('network vnet create -g {rg} -n {vnet}')
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet} -n {subnet} --address-prefix 10.0.0.0/24')
        self.cmd('network nic create -g {rg} -n {nic} --vnet-name {vnet} --subnet {subnet}')

        # prepare workspace
        workspace = self.cmd('monitor log-analytics workspace create '
                             '--resource-group {rg} '
                             '--location eastus '
                             '--workspace-name {workspace} ').get_output_in_json()
        self.kwargs.update({
            'workspace_id': workspace['id']
        })

        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--vnet {vnet} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        res1 = self.cmd('network watcher flow-log show --location {location} --name {flow_log}').get_output_in_json()
        self.assertEqual(res1['name'], self.kwargs['flow_log'])
        self.assertEqual(res1['enabled'], True)
        self.assertEqual(res1['retentionPolicy']['days'], 0)
        self.assertEqual(res1['retentionPolicy']['enabled'], False)
        # self.assertIsNone(res1['tags'])

        #update targetId from vnet to nic
        res2 = self.cmd('network watcher flow-log update '
                        '--location {location} '
                        '--name {flow_log} '
                        '--nic {nic} '
                        '--resource-group {rg} '
                        '--retention 2 '
                        '--tags foo=bar ').get_output_in_json()
        self.assertEqual(res2['name'], self.kwargs['flow_log'])
        self.assertEqual(res2['enabled'], True)
        self.assertTrue(res2['targetResourceId'].endswith(self.kwargs['nic']))
        self.assertEqual(res2['name'], self.kwargs['flow_log'])
        self.assertEqual(res2['retentionPolicy']['days'], 2)
        self.assertEqual(res2['retentionPolicy']['enabled'], True)
        # self.assertIsNotNone(res2['tags'])
        
        self.cmd('network watcher flow-log delete --location {location} --name {flow_log}')

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('network watcher flow-log show --location {location} --name {flow_log}')

        #targetId as subnet
        self.cmd('network watcher flow-log create '
                 '--location {location} '
                 '--resource-group {rg} '
                 '--vnet {vnet} '
                 '--subnet {subnet} '
                 '--storage-account {storage_account} '
                 '--workspace {workspace_id} '
                 '--name {flow_log} ')

        res1 = self.cmd('network watcher flow-log show --location {location} --name {flow_log}').get_output_in_json()
        self.assertEqual(res1['name'], self.kwargs['flow_log'])
        self.assertEqual(res1['enabled'], True)
        self.assertEqual(res1['retentionPolicy']['days'], 0)
        self.assertEqual(res1['retentionPolicy']['enabled'], False)
        # self.assertIsNone(res1['tags'])

        #update targetId from subnet to nsg
        res2 = self.cmd('network watcher flow-log update '
                        '--location {location} '
                        '--name {flow_log} '
                        '--nsg {nsg} '
                        '--resource-group {rg} '
                        '--retention 2 '
                        '--tags foo=bar ').get_output_in_json()
        self.assertEqual(res2['name'], self.kwargs['flow_log'])
        self.assertEqual(res2['enabled'], True)
        self.assertTrue(res2['targetResourceId'].endswith(self.kwargs['nsg']))
        self.assertEqual(res2['name'], self.kwargs['flow_log'])
        self.assertEqual(res2['retentionPolicy']['days'], 2)
        self.assertEqual(res2['retentionPolicy']['enabled'], True)
        self.assertIsNotNone(res2['tags'])

        self.cmd('network watcher flow-log delete --location {location} --name {flow_log}')

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('network watcher flow-log show --location {location} --name {flow_log}')

        #targetId as NSG
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
        # self.assertIsNone(res1['tags'])

        #update targetId from nsg to vnet
        res2 = self.cmd('network watcher flow-log update '
                        '--location {location} '
                        '--name {flow_log} '
                        '--vnet {vnet} '
                        '--resource-group {rg} '
                        '--retention 2 '
                        '--tags foo=bar ').get_output_in_json()
        self.assertEqual(res2['name'], self.kwargs['flow_log'])
        self.assertEqual(res2['enabled'], True)
        self.assertTrue(res2['targetResourceId'].endswith(self.kwargs['vnet']))
        self.assertEqual(res2['name'], self.kwargs['flow_log'])
        self.assertEqual(res2['retentionPolicy']['days'], 2)
        self.assertEqual(res2['retentionPolicy']['enabled'], True)
        self.assertIsNotNone(res2['tags'])
        
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
        # self.assertIsNone(res1['tags'])

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
