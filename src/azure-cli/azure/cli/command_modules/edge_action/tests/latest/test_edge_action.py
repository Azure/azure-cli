# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck, ScenarioTest


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class EdgeActionScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='clitests', location='eastus', additional_tags={'owner': 'edgeaction'})
    def test_edge_action_crud(self, resource_group):
        """Test Edge Action CRUD operations"""
        edge_action_name = self.create_random_name(prefix='edgeaction', length=20)

        # Test list edge actions (should be empty initially)
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.cmd('edge-action list -g {}'.format(resource_group), checks=list_checks)

        # Test create edge action
        create_checks = [
            JMESPathCheck('name', edge_action_name),
            JMESPathCheck('resourceGroup', resource_group)
        ]
        self.cmd('edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(
            resource_group, edge_action_name), checks=create_checks)

        # Test show edge action
        show_checks = [
            JMESPathCheck('name', edge_action_name),
            JMESPathCheck('resourceGroup', resource_group)
        ]
        self.cmd('edge-action show -g {} -n {}'.format(resource_group, edge_action_name), checks=show_checks)

        # Test list edge actions (should contain 1 item now)
        list_checks = [JMESPathCheck('length(@)', 1)]
        self.cmd('edge-action list -g {}'.format(resource_group), checks=list_checks)

        # Test update edge action
        self.cmd('edge-action update -g {} -n {} --tags test=value'.format(
            resource_group, edge_action_name))

        # Test delete edge action
        self.cmd('edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))

        # Verify deletion - list should be empty again
        list_checks = [JMESPathCheck('length(@)', 0)]
        self.cmd('edge-action list -g {}'.format(resource_group), checks=list_checks)

    @ResourceGroupPreparer(additional_tags={'owner': 'edgeaction'})
    def test_edge_action_version_operations(self, resource_group):
        """Test Edge Action Version operations"""
        edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
        version_name = 'v1'

        # Create edge action first
        self.cmd('edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(
            resource_group, edge_action_name))

        # Test create version
        create_version_checks = [
            JMESPathCheck('name', version_name)
        ]
        self.cmd('edge-action version create -g {} --edge-action-name {} -n {} --deployment-type file --location global --is-default-version False'.format(
            resource_group, edge_action_name, version_name), checks=create_version_checks)

        # Test show version
        self.cmd('edge-action version show -g {} --edge-action-name {} -n {}'.format(
            resource_group, edge_action_name, version_name))

        # Test list versions
        list_version_checks = [JMESPathCheck('length(@)', 1)]
        self.cmd('edge-action version list -g {} --edge-action-name {}'.format(
            resource_group, edge_action_name), checks=list_version_checks)

        # Test delete version
        self.cmd('edge-action version delete -g {} --edge-action-name {} -n {} -y'.format(
            resource_group, edge_action_name, version_name))

        # Clean up edge action
        self.cmd('edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))

    @ResourceGroupPreparer(additional_tags={'owner': 'edgeaction'})
    def test_edge_action_version_deploy_with_file(self, resource_group):
        """Test Edge Action Version deployment with file path using custom command"""
        edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
        version_name = 'v1'

        # Create edge action and version
        self.cmd('edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(
            resource_group, edge_action_name))
        self.cmd('edge-action version create -g {} --edge-action-name {} -n {} --deployment-type file --location global --is-default-version False'.format(
            resource_group, edge_action_name, version_name))

        # Use test fixture file
        test_file = os.path.join(TEST_DIR, 'test_files', 'sample_edge_action.js')

        # Test deploy with file path using custom deploy-from-file command (file mode)
        self.cmd('edge-action version deploy-from-file -g {} --edge-action-name {} --version {} --file-path "{}" --deployment-type file'.format(
            resource_group, edge_action_name, version_name, test_file))

        # Clean up
        self.cmd('edge-action version delete -g {} --edge-action-name {} -n {} -y'.format(
            resource_group, edge_action_name, version_name))
        self.cmd('edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))

    @ResourceGroupPreparer(additional_tags={'owner': 'edgeaction'})
    def test_edge_action_version_deploy_with_zip(self, resource_group):
        """Test Edge Action Version deployment with zip file using custom command"""
        edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
        version_name = 'v1'

        # Create edge action and version
        self.cmd('edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(
            resource_group, edge_action_name))
        self.cmd('edge-action version create -g {} --edge-action-name {} -n {} --deployment-type zip --location global --is-default-version False'.format(
            resource_group, edge_action_name, version_name))

        # Use test fixture zip file
        test_zip = os.path.join(TEST_DIR, 'test_files', 'sample_edge_action.zip')

        # Test deploy with zip file path using custom deploy-from-file command (auto-detects zip)
        self.cmd('edge-action version deploy-from-file -g {} --edge-action-name {} --version {} --file-path "{}"'.format(
            resource_group, edge_action_name, version_name, test_zip))

        # Clean up
        self.cmd('edge-action version delete -g {} --edge-action-name {} -n {} -y'.format(
            resource_group, edge_action_name, version_name))
        self.cmd('edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))

    @ResourceGroupPreparer(additional_tags={'owner': 'edgeaction'})
    def test_edge_action_version_deploy_with_content(self, resource_group):
        """Test Edge Action Version deployment with base64 content (backward compatibility)"""
        edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
        version_name = 'v1'

        # Create edge action and version
        self.cmd('edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(
            resource_group, edge_action_name))
        self.cmd('edge-action version create -g {} --edge-action-name {} -n {} --deployment-type file --location global --is-default-version False'.format(
            resource_group, edge_action_name, version_name))

        # Test deploy with base64 content
        import base64
        test_content = base64.b64encode(b'function handler(event) { return event; }').decode('utf-8')
        self.cmd('edge-action version deploy-version-code -g {} --edge-action-name {} --version {} --name testcode --content "{}"'.format(
            resource_group, edge_action_name, version_name, test_content))

        # Clean up
        self.cmd('edge-action version delete -g {} --edge-action-name {} -n {} -y'.format(
            resource_group, edge_action_name, version_name))
        self.cmd('edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))
