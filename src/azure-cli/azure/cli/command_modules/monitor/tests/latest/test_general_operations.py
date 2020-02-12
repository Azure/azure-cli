# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer

class MonitorGeneralScenarios(ScenarioTest):
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

        vm1_json = self.cmd('vm create -g {rg} -n {vm1} --image UbuntuLTS --admin-password TestPassword11!! --admin-username '
                           'testadmin --authentication-type password').get_output_in_json()
        vm2_json = self.cmd('vm create -g {rg} -n {vm2} --image UbuntuLTS --admin-password TestPassword11!! --admin-username '
                           'testadmin --authentication-type password').get_output_in_json()
        self.kwargs.update({
            'vm1_id': vm1_json['id'],
            'vm2_id': vm2_json['id']
        })
        self.cmd('monitor action-group create -g {rg} -n {ag1}')
        self.cmd('monitor metrics alert create -g {rg} -n {alert} --scopes {vm1_id} --action {ag1} --condition "avg Percentage CPU > 90" --description "High CPU"', checks=[
            self.check('description', 'High CPU'),
            self.check('severity', 2),
            self.check('autoMitigate', None),
            self.check('windowSize', '0:05:00'),
            self.check('evaluationFrequency', '0:01:00'),
            self.check('length(scopes)', 1)
        ])

        self.cmd('monitor clone --source-resource {vm1_id} --target-resource {vm2_id}', checks=[
            self.check('description', 'High CPU'),
            self.check('severity', 2),
            self.check('autoMitigate', None),
            self.check('windowSize', '0:05:00'),
            self.check('evaluationFrequency', '0:01:00'),
            self.check('length(scopes)', 2)
        ])
