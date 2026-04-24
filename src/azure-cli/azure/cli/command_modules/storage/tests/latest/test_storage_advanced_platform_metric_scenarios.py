# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer)
from ..storage_test_util import StorageScenarioMixin


class StorageAdvancedPlatformMetricTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_storage_advanced_platform_metric')
    @StorageAccountPreparer()
    def test_storage_advanced_platform_metric(self, resource_group, storage_account):
        kwargs = {
            'rg': resource_group,
            'sa': storage_account
        }
        self.cmd('storage advanced-platform-metric create -g {rg} --account-name {sa} --enabled '
                 '--rule-config-filter-type AllContainersFilter'.format(**kwargs),
                 checks=[
                     JMESPathCheck('properties.ruleConfig.filterType', 'AllContainersFilter'),
                     JMESPathCheck('properties.enabled', True)])

        self.cmd('storage advanced-platform-metric show -g {rg} --account-name {sa}')

        self.cmd('storage advanced-platform-metric update -g {rg} --account-name {sa} --enabled '
                 '--rule-config-filter-type ContainerPrefixFilter '
                 '--rule-config-filter-values logs data'.format(**kwargs),
                 checks=[
                     JMESPathCheck('properties.ruleConfig.filterType', 'ContainerPrefixFilter'),
                     JMESPathCheck('properties.ruleConfig.filterValues', ['logs', 'data'])])

        self.cmd('storage advanced-platform-metric list -g {rg} --account-name {sa}',
                 checks=JMESPathCheck('length(@)', 1))

        self.cmd('storage advanced-platform-metric delete -g {rg} --account-name {sa} --yes')

        self.cmd('storage advanced-platform-metric create -g {rg} --account-name {sa} --enabled '
                 '--rule-config-filter-type ContainerPrefixFilter '
                 '--rule-config-filter-values logs data'.format(**kwargs),
                 checks=[
                     JMESPathCheck('properties.ruleConfig.filterType', 'ContainerPrefixFilter'),
                     JMESPathCheck('properties.ruleConfig.filterValues', ['logs', 'data'])])

        self.cmd('storage advanced-platform-metric update -g {rg} --account-name {sa} --enabled '
                 '--rule-config-filter-type ContainerListFilter '
                 '--rule-config-filter-values logs1 data1'.format(**kwargs),
                 checks=[
                     JMESPathCheck('properties.ruleConfig.filterType', 'ContainerListFilter'),
                     JMESPathCheck('properties.ruleConfig.filterValues', ['logs1', 'data1'])])

        self.cmd('storage advanced-platform-metric delete -g {rg} --account-name {sa} --yes')

        self.cmd('storage advanced-platform-metric create -g {rg} --account-name {sa} --enabled '
                 '--rule-config-filter-type ContainerListFilter '
                 '--rule-config-filter-values logs data'.format(**kwargs),
                 checks=[
                     JMESPathCheck('properties.ruleConfig.filterType', 'ContainerListFilter'),
                     JMESPathCheck('properties.ruleConfig.filterValues', ['logs', 'data'])])

        self.cmd('storage advanced-platform-metric update -g {rg} --account-name {sa} --enabled '
                 '--rule-config-filter-type AllContainersFilter'.format(**kwargs),
                 checks=[
                     JMESPathCheck('properties.ruleConfig.filterType', 'AllContainersFilter')])
