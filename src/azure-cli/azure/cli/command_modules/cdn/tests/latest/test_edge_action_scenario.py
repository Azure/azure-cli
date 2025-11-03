# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck, ScenarioTest
from .scenario_mixin import CdnScenarioMixin
from .afdx_scenario_mixin import CdnAfdScenarioMixin


class CdnEdgeActionScenarioTest(CdnScenarioMixin, CdnAfdScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_edge_action_crud(self, resource_group):
        """Test Edge Action CRUD operations"""
        edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
        
        # Test list edge actions (should be empty initially)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.cmd('cdn edge-action list -g {}'.format(resource_group), checks=list_checks)
        
        # Test create edge action
        create_checks = [
            JMESPathCheck('name', edge_action_name),
            JMESPathCheck('resourceGroup', resource_group)
        ]
        self.cmd('cdn edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(resource_group, edge_action_name),
                 checks=create_checks)
        
        # Test show edge action
        show_checks = [
            JMESPathCheck('name', edge_action_name),
            JMESPathCheck('resourceGroup', resource_group)
        ]
        self.cmd('cdn edge-action show -g {} -n {}'.format(resource_group, edge_action_name),
                 checks=show_checks)
        
        # Test list edge actions (should contain 1 item now)
        list_checks = [JMESPathCheck('length(@)', 1)]
        self.cmd('cdn edge-action list -g {}'.format(resource_group), checks=list_checks)
        
        # Test update edge action
        self.cmd('cdn edge-action update -g {} -n {} --tags test=value'.format(
            resource_group, edge_action_name))
        
        # Test delete edge action
        self.cmd('cdn edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))
        
        # Verify deletion - list should be empty again
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.cmd('cdn edge-action list -g {}'.format(resource_group), checks=list_checks)

    @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    def test_edge_action_version_operations(self, resource_group):
        """Test Edge Action Version operations"""
        edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
        version_name = 'v1'
        
        # Create edge action first
        self.cmd('cdn edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(resource_group, edge_action_name))
        
        # Test create version
        create_version_checks = [
            JMESPathCheck('name', version_name)
        ]
        self.cmd('cdn edge-action version create -g {} --edge-action-name {} -n {} --deployment-type file --location global --is-default-version False'.format(
            resource_group, edge_action_name, version_name), checks=create_version_checks)
        
        # Test show version
        self.cmd('cdn edge-action version show -g {} --edge-action-name {} -n {}'.format(
            resource_group, edge_action_name, version_name))
        
        # Test list versions
        list_version_checks = [JMESPathCheck('length(@)', 1)]
        self.cmd('cdn edge-action version list -g {} --edge-action-name {}'.format(
            resource_group, edge_action_name), checks=list_version_checks)
        
        # Test delete version
        self.cmd('cdn edge-action version delete -g {} --edge-action-name {} -n {} -y'.format(
            resource_group, edge_action_name, version_name))
        
        # Clean up edge action
        self.cmd('cdn edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))

    # @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    # def test_edge_action_execution_filter_operations(self, resource_group):
    #     """Test Edge Action Execution Filter operations"""
    #     edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
    #     filter_name = self.create_random_name(prefix='filter', length=15)
        
    #     # Create edge action first
    #     self.cmd('cdn edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(resource_group, edge_action_name))

    #     version_name = 'v1'
    #     # Test create version
    #     create_version_checks = [
    #         JMESPathCheck('name', version_name)
    #     ]
    #     self.cmd('cdn edge-action version create -g {} --edge-action-name {} -n {} --deployment-type file --location global --is-default-version False'.format(
    #         resource_group, edge_action_name, version_name), checks=create_version_checks)
        
    #     version_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Cdn/EdgeActions/{}/versions/v1".format(
    #         self.get_subscription_id(), resource_group, edge_action_name)
    #     # Test create execution filter
    #     create_filter_checks = [
    #         JMESPathCheck('name', filter_name)
    #     ]
    #     self.cmd('cdn edge-action execution-filter create -g {} --location global --edge-action-name {} -n {} --version-id {} --execution-filter-identifier-header-name test-name --execution-filter-identifier-header-value test-value'.format(
    #         resource_group, edge_action_name, filter_name, version_id), checks=create_filter_checks)
        
    #     # Test show execution filter
    #     self.cmd('cdn edge-action execution-filter show -g {} --edge-action-name {} -n {}'.format(
    #         resource_group, edge_action_name, filter_name))
        
    #     # Test list execution filters
    #     list_filter_checks = [JMESPathCheck('length(@)', 1)]
    #     self.cmd('cdn edge-action execution-filter list -g {} --edge-action-name {}'.format(
    #         resource_group, edge_action_name), checks=list_filter_checks)
        
    #     # Test delete execution filter
    #     self.cmd('cdn edge-action execution-filter delete -g {} --edge-action-name {} -n {} -y'.format(
    #         resource_group, edge_action_name, filter_name))
        
    #     # Clean up edge action
    #     self.cmd('cdn edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))

    # @ResourceGroupPreparer(additional_tags={'owner': 'jingnanxu'})
    # def test_edge_action_attachment_operations(self, resource_group):
    #     """Test Edge Action Attachment operations"""
    #     edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
        
    #     # Create AFD profile, rule set and rule for attachment
    #     profile_name = self.create_random_name(prefix='profile', length=16)
    #     rule_set_name = self.create_random_name(prefix='ruleset', length=16)
    #     rule_name = self.create_random_name(prefix='rule', length=16)
        
    #     # Create AFD profile
    #     self.afd_profile_create_cmd(resource_group, profile_name)
        
    #     # Create rule set
    #     self.afd_rule_set_add_cmd(resource_group, rule_set_name, profile_name)
        
    #     # Create a simple rule
    #     self.afd_rule_add_cmd(resource_group,
    #                           rule_set_name,
    #                           rule_name,
    #                           profile_name,
    #                           options='--match-processing-behavior Stop --action-name RouteConfigurationOverride --enable-caching True --query-string-caching-behavior UseQueryString --cache-behavior HonorOrigin --order 1')
        
    #     # Construct the rule resource ID
    #     attached_resource_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Cdn/profiles/{}/ruleSets/{}/rules/{}".format(
    #         self.get_subscription_id(), resource_group, profile_name, rule_set_name, rule_name)
        
    #     # Create edge action
    #     self.cmd('cdn edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(resource_group, edge_action_name))

    #     version_name = 'v1'

    #     create_version_checks = [
    #         JMESPathCheck('name', version_name)
    #     ]
    #     self.cmd('cdn edge-action version create -g {} --edge-action-name {} -n {} --deployment-type file --location global --is-default-version False'.format(
    #         resource_group, edge_action_name, version_name), checks=create_version_checks)
        
    #     # Test add attachment
    #     self.cmd('cdn edge-action add-attachment -g {} --edge-action-name {} --attached-resource-id "{}"'.format(
    #         resource_group, edge_action_name, attached_resource_id))
        
    #     # # Test delete attachment
    #     # self.cmd('cdn edge-action delete-attachment -g {} --edge-action-name {} --attached-resource-id "{}" -y'.format(
    #     #     resource_group, edge_action_name, attached_resource_id))

    #     # Test delete version
    #     self.cmd('cdn edge-action version delete -g {} --edge-action-name {} -n {} -y'.format(
    #         resource_group, edge_action_name, version_name))
        
    #     # Clean up edge action (AFD resources will be cleaned up automatically by ResourceGroupPreparer)
    #     self.cmd('cdn edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))

