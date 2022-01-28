# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, live_only
from azure.cli.testsdk.constants import AUX_SUBSCRIPTION
from unittest import mock
import unittest
from msrestazure.tools import resource_id


class MonitorCloneVMScenarios(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    def test_monitor_clone_vm_metric_alerts_scenario(self, resource_group):
        self.kwargs.update({
            'alert': 'alert1',
            'vm1': 'vm1',
            'vm2': 'vm2',
            'vm3': 'vm3',
            'ag1': 'ag1',
            'rg': resource_group
        })

        vm1_json = self.cmd('vm create -g {rg} -n {vm1} --image UbuntuLTS --admin-password TestPassword11!! '
                            '--admin-username testadmin --authentication-type password').get_output_in_json()
        vm2_json = self.cmd('vm create -g {rg} -n {vm2} --image UbuntuLTS --admin-password TestPassword11!! '
                            '--admin-username testadmin --authentication-type password').get_output_in_json()
        vm3_json = self.cmd('vm create -g {rg} -n {vm3} --image UbuntuLTS --admin-password TestPassword11!! '
                            '--admin-username testadmin --authentication-type password').get_output_in_json()
        self.kwargs.update({
            'vm1_id': vm1_json['id'],
            'vm2_id': vm2_json['id'],
            'vm3_id': vm3_json['id']
        })
        self.cmd('monitor action-group create -g {rg} -n {ag1}')
        self.cmd('monitor metrics alert create -g {rg} -n {alert} --scopes {vm1_id} {vm2_id} --action {ag1} --region eastus --condition "avg Percentage CPU > 90" --description "High CPU"', checks=[
            self.check('description', 'High CPU'),
            self.check('severity', 2),
            self.check('autoMitigate', None),
            self.check('windowSize', '0:05:00'),
            self.check('evaluationFrequency', '0:01:00'),
            self.check('length(scopes)', 2)
        ])
        with mock.patch('azure.cli.command_modules.monitor.operations.monitor_clone_util.gen_guid', side_effect=self.create_guid):
            self.cmd('monitor clone --source-resource {vm1_id} --target-resource {vm3_id}', checks=[
                self.check('metricsAlert[0].description', 'High CPU'),
                self.check('metricsAlert[0].severity', 2),
                self.check('metricsAlert[0].autoMitigate', None),
                self.check('metricsAlert[0].windowSize', '0:05:00'),
                self.check('metricsAlert[0].evaluationFrequency', '0:01:00'),
                self.check('length(metricsAlert[0].scopes)', 3)
            ])


class MonitorCloneStorageAccountScenarios(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_metric_alert_clone')
    @StorageAccountPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_2')
    def test_monitor_clone_storage_metric_alerts_scenario(self, resource_group, storage_account, storage_account_2):
        self.kwargs.update({
            'alert': 'alert1',
            'sa': storage_account,
            'ag1': 'ag1',
            'sub': self.get_subscription_id(),
            'sa_id': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=storage_account,
                namespace='Microsoft.Storage',
                type='storageAccounts'),
            'sa_id_2': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=storage_account_2,
                namespace='Microsoft.Storage',
                type='storageAccounts'),
        })

        self.cmd('monitor action-group create -g {rg} -n {ag1}')
        self.cmd('monitor metrics alert create -g {rg} -n {alert} --scopes {sa_id} --region westus --action {ag1} --description "Test" --condition "total transactions > 5 where ResponseType includes Success and ApiName includes GetBlob" --condition "avg SuccessE2ELatency > 250 where ApiName includes GetBlob"', checks=[
            self.check('description', 'Test'),
            self.check('severity', 2),
            self.check('autoMitigate', None),
            self.check('windowSize', '0:05:00'),
            self.check('evaluationFrequency', '0:01:00'),
            self.check('length(criteria.allOf)', 2),
            self.check('length(criteria.allOf[0].dimensions)', 2),
            self.check('length(criteria.allOf[1].dimensions)', 1)
        ])

        with mock.patch('azure.cli.command_modules.monitor.operations.monitor_clone_util.gen_guid', side_effect=self.create_guid):
            self.cmd('monitor clone --source-resource {sa_id} --target-resource {sa_id_2}', checks=[
                self.check('metricsAlert[0].description', 'Test'),
                self.check('metricsAlert[0].severity', 2),
                self.check('metricsAlert[0].autoMitigate', None),
                self.check('metricsAlert[0].windowSize', '0:05:00'),
                self.check('metricsAlert[0].evaluationFrequency', '0:01:00'),
                self.check('length(metricsAlert[0].criteria.allOf)', 2),
                self.check('length(metricsAlert[0].criteria.allOf[0].dimensions)', 2),
                self.check('length(metricsAlert[0].criteria.allOf[1].dimensions)', 1),
            ])


class MonitorCloneStorageAccountAlwaysScenarios(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_metric_alert_clone')
    @StorageAccountPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_2')
    def test_monitor_clone_storage_metric_alerts_always_scenario(self, resource_group, storage_account, storage_account_2):
        self.kwargs.update({
            'alert': 'alert1',
            'sa': storage_account,
            'ag1': 'ag1',
            'sub': self.get_subscription_id(),
            'sa_id': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=storage_account,
                namespace='Microsoft.Storage',
                type='storageAccounts'),
            'sa_id_2': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=storage_account_2,
                namespace='Microsoft.Storage',
                type='storageAccounts'),
        })

        self.cmd('monitor action-group create -g {rg} -n {ag1}')
        self.cmd('monitor metrics alert create -g {rg} -n {alert} --scopes {sa_id} --region westus --action {ag1} --description "Test" --condition "total transactions > 5 where ResponseType includes Success and ApiName includes GetBlob" --condition "avg SuccessE2ELatency > 250 where ApiName includes GetBlob"', checks=[
            self.check('description', 'Test'),
            self.check('severity', 2),
            self.check('autoMitigate', None),
            self.check('windowSize', '0:05:00'),
            self.check('evaluationFrequency', '0:01:00'),
            self.check('length(criteria.allOf)', 2),
            self.check('length(criteria.allOf[0].dimensions)', 2),
            self.check('length(criteria.allOf[1].dimensions)', 1)
        ])

        with mock.patch('azure.cli.command_modules.monitor.operations.monitor_clone_util.gen_guid', side_effect=self.create_guid):
            self.cmd('monitor clone --source-resource {sa_id} --target-resource {sa_id_2} --always-clone', checks=[
                self.check('metricsAlert[0].description', 'Test'),
                self.check('metricsAlert[0].severity', 2),
                self.check('metricsAlert[0].autoMitigate', None),
                self.check('metricsAlert[0].windowSize', '0:05:00'),
                self.check('metricsAlert[0].evaluationFrequency', '0:01:00'),
                self.check('length(metricsAlert[0].criteria.allOf)', 2),
                self.check('length(metricsAlert[0].criteria.allOf[0].dimensions)', 2),
                self.check('length(metricsAlert[0].criteria.allOf[1].dimensions)', 1),
            ])


class MonitorClonePublicIpScenarios(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_metric_alert_clone')
    def test_monitor_clone_public_ip_metric_alerts_scenario(self, resource_group):
        self.kwargs.update({
            'alert': 'alert1',
            'alert2': 'alert2',
            'ag1': 'ag1',
            'sub': self.get_subscription_id(),
            'rg': resource_group,
            'ip1': 'ip1',
            'ip2': 'ip2'
        })

        ip1_json = self.cmd('network public-ip create -g {rg} -n {ip1}').get_output_in_json()
        ip2_json = self.cmd('network public-ip create -g {rg} -n {ip2}').get_output_in_json()
        self.kwargs.update({
            'ip1_id': ip1_json['publicIp']['id'],
            'ip2_id': ip2_json['publicIp']['id']
        })

        self.cmd('monitor action-group create -g {rg} -n {ag1}')
        self.cmd('monitor metrics alert create -g {rg} -n {alert} --scopes {ip1_id} --region westus --action {ag1} --description "Test" --condition "total TCPBytesForwardedDDoS > 5"', checks=[
            self.check('description', 'Test'),
            self.check('severity', 2),
            self.check('windowSize', '0:05:00'),
            self.check('evaluationFrequency', '0:01:00'),
            self.check('length(scopes)', 1)
        ])

        self.cmd('monitor metrics alert create -g {rg} -n {alert2} --scopes {ip1_id} --region westus --action {ag1} --description "Test2" --condition "max TCPBytesForwardedDDoS > 5"', checks=[
            self.check('description', 'Test2'),
            self.check('severity', 2),
            self.check('windowSize', '0:05:00'),
            self.check('evaluationFrequency', '0:01:00'),
            self.check('length(scopes)', 1)
        ])

        with mock.patch('azure.cli.command_modules.monitor.operations.monitor_clone_util.gen_guid', side_effect=self.create_guid):
            self.cmd('monitor clone --source-resource {ip1_id} --target-resource {ip2_id}', checks=[
                self.check('length(metricsAlert)', 2),
            ])


class MonitorCloneStorageAccountAcrossSubsScenarios(ScenarioTest):
    @unittest.skip('Accross subs are not supported now.')
    # @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_metric_alert_clone')
    @ResourceGroupPreparer(name_prefix='cli_test_metric_alert_clone',
                           parameter_name='another_resource_group', subscription=AUX_SUBSCRIPTION)
    def test_monitor_clone_storage_metric_alerts_across_subs_scenario(self, resource_group, another_resource_group):
        self.kwargs.update({
            'alert': 'alert1',
            'sa': self.create_random_name('sa', 24),
            'sa2': self.create_random_name('sa', 24),
            'ag1': 'ag1',
            'rg': resource_group,
            'ext_sub': AUX_SUBSCRIPTION,
            'ext_rg': another_resource_group,
        })

        sa1_json = self.cmd('storage account create -n {sa} -g {ext_rg} -l eastus --sku Standard_LRS --kind Storage --subscription {ext_sub}').get_output_in_json()
        sa2_json = self.cmd('storage account create -n {sa2} -g {rg} -l eastus --sku Standard_LRS --kind Storage').get_output_in_json()
        self.kwargs.update({
            'sa_id': sa1_json['id'],
            'sa_id_2': sa2_json['id'],
        })
        self.cmd('monitor action-group create -g {ext_rg} -n {ag1} --subscription {ext_sub}')
        self.cmd('monitor metrics alert create -g {ext_rg} --subscription {ext_sub} -n {alert} '
                 '--scopes {sa_id} --action {ag1} --description "Test" '
                 '--condition "total transactions > 5 where ResponseType includes Success and ApiName includes GetBlob" '
                 '--condition "avg SuccessE2ELatency > 250 where ApiName includes GetBlob"',
                 checks=[
                     self.check('description', 'Test'),
                     self.check('severity', 2),
                     self.check('autoMitigate', None),
                     self.check('windowSize', '0:05:00'),
                     self.check('evaluationFrequency', '0:01:00'),
                     self.check('length(criteria.allOf)', 2),
                     self.check('length(criteria.allOf[0].dimensions)', 2),
                     self.check('length(criteria.allOf[1].dimensions)', 1)
                 ])

        with mock.patch('azure.cli.command_modules.monitor.operations.monitor_clone_util.gen_guid', side_effect=self.create_guid):
            self.cmd('monitor clone --source-resource {sa_id} --target-resource {sa_id_2}', checks=[
                self.check('metricsAlert[0].description', 'Test'),
                self.check('metricsAlert[0].severity', 2),
                self.check('metricsAlert[0].autoMitigate', None),
                self.check('metricsAlert[0].windowSize', '0:05:00'),
                self.check('metricsAlert[0].evaluationFrequency', '0:01:00'),
                self.check('length(metricsAlert[0].criteria.allOf)', 2),
                self.check('length(metricsAlert[0].criteria.allOf[0].dimensions)', 2),
                self.check('length(metricsAlert[0].criteria.allOf[1].dimensions)', 1),
            ])
