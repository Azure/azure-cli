# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer


class TestMonitorDiagnosticSettings(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer(location='southcentralus')
    def test_monitor_diagnostic_settings_scenario(self, resource_group, storage_account):
        nsg_name = self.create_random_name(prefix='nsg', length=16)
        self.cmd('network nsg create -n {} -g {}'.format(nsg_name, resource_group))

        log_config = json.dumps([
            {
                "category": "NetworkSecurityGroupEvent",
                "enabled": True,
                "retentionPolicy": {"days": 0, "enabled": False}
            },
            {
                "category": "NetworkSecurityGroupRuleCounter",
                "enabled": True,
                "retentionPolicy": {"days": 0, "enabled": False}
            }
        ])

        self.cmd('monitor diagnostic-settings create -n test01 '
                 '--resource {} '
                 '--resource-type Microsoft.Network/networkSecurityGroups '
                 '--resource-group {} '
                 '--storage-account {} '
                 '--log \'{}\' -o json'
                 ''.format(nsg_name, resource_group, storage_account, log_config)).assert_with_checks(
            JMESPathCheck('name', 'test01')
        )

        self.cmd('monitor diagnostic-settings list '
                 '--resource {} '
                 '--resource-type Microsoft.Network/networkSecurityGroups '
                 '--resource-group {} -o json'.format(nsg_name, resource_group)).assert_with_checks(
            JMESPathCheck('length(value)', 1),
            JMESPathCheck('value[0].name', 'test01')
        )

        self.cmd('monitor diagnostic-settings show -n test01 '
                 '--resource {} '
                 '--resource-type Microsoft.Network/networkSecurityGroups '
                 '--resource-group {} -o json'.format(nsg_name, resource_group)).assert_with_checks(
            JMESPathCheck('name', 'test01')
        )

        self.cmd('monitor diagnostic-settings delete -n test01 '
                 '--resource {} '
                 '--resource-type Microsoft.Network/networkSecurityGroups '
                 '--resource-group {} -o json'.format(nsg_name, resource_group))

        self.cmd('monitor diagnostic-settings list '
                 '--resource {} '
                 '--resource-type Microsoft.Network/networkSecurityGroups '
                 '--resource-group {} -o json'.format(nsg_name, resource_group)).assert_with_checks(
            JMESPathCheck('length(value)', 0)
        )


if __name__ == '__main__':
    import unittest

    unittest.main()
