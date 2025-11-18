# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
from azure.cli.testsdk import ResourceGroupPreparer, JMESPathCheck, ScenarioTest


class EdgeActionScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(additional_tags={'owner': 'edgeaction'})
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
        """Test Edge Action Version deployment with file path"""
        edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
        version_name = 'v1'

        # Create edge action and version
        self.cmd('edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(
            resource_group, edge_action_name))
        self.cmd('edge-action version create -g {} --edge-action-name {} -n {} --deployment-type file --location global --is-default-version False'.format(
            resource_group, edge_action_name, version_name))

        # Create a temporary JavaScript file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write('console.log("Hello from Edge Action");')
            temp_file = f.name

        try:
            # Test deploy with file path (file mode)
            self.cmd('edge-action version deploy-version-code -g {} --edge-action-name {} --version {} --file-path {} --file-type file'.format(
                resource_group, edge_action_name, version_name, temp_file))
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)

        # Clean up
        self.cmd('edge-action version delete -g {} --edge-action-name {} -n {} -y'.format(
            resource_group, edge_action_name, version_name))
        self.cmd('edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))

    @ResourceGroupPreparer(additional_tags={'owner': 'edgeaction'})
    def test_edge_action_version_deploy_with_zip(self, resource_group):
        """Test Edge Action Version deployment with zip file"""
        edge_action_name = self.create_random_name(prefix='edgeaction', length=20)
        version_name = 'v1'

        # Create edge action and version
        self.cmd('edge-action create -g {} -n {} --sku name=Standard tier=Standard --location global'.format(
            resource_group, edge_action_name))
        self.cmd('edge-action version create -g {} --edge-action-name {} -n {} --deployment-type file --location global --is-default-version False'.format(
            resource_group, edge_action_name, version_name))

        # Create a temporary file to zip
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write('console.log("Hello from zipped Edge Action");')
            temp_file = f.name

        try:
            # Test deploy with file path (zip mode - will create zip)
            self.cmd('edge-action version deploy-version-code -g {} --edge-action-name {} --version {} --file-path {} --file-type zip'.format(
                resource_group, edge_action_name, version_name, temp_file))
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)

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

        # Test deploy with base64 content (original method)
        import base64
        test_content = base64.b64encode(b'console.log("test");').decode('utf-8')
        self.cmd('edge-action version deploy-version-code -g {} --edge-action-name {} --version {} --name testcode --content "{}"'.format(
            resource_group, edge_action_name, version_name, test_content))

        # Clean up
        self.cmd('edge-action version delete -g {} --edge-action-name {} -n {} -y'.format(
            resource_group, edge_action_name, version_name))
        self.cmd('edge-action delete -g {} -n {} -y'.format(resource_group, edge_action_name))
