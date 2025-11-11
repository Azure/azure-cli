# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import patch, Mock
import azure.cli.command_modules.acs.managednamespace as ns
from azure.cli.command_modules.acs.tests.latest.mocks import MockCLI, MockCmd
from azure.cli.core.azclierror import (
    InvalidArgumentValueError,
    RequiredArgumentMissingError,
)

@patch("azure.cli.command_modules.acs.managednamespace.get_container_service_client")
class TestAddManagedNamespace(unittest.TestCase):
    def setUp(self):
        # Set up mock cluster client and location
        self.mock_cluster = Mock()
        self.mock_cluster.location = "eastus"

        self.mock_managed_clusters = Mock()
        self.mock_managed_clusters.get.return_value = self.mock_cluster

        self.mock_client = Mock()
        self.mock_client.managed_clusters = self.mock_managed_clusters

    def test_add_managed_namespace_with_invalid_labels(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "labels": "x",
        }
        err = "Invalid format 'x'. Expected format key=value."
        with self.assertRaises(ValueError) as cm:
            ns.aks_managed_namespace_add(cmd, None, raw_parameters, None, False)
        self.assertEqual(str(cm.exception), err)
    
    def test_add_managed_namespace_with_invalid_annotations(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "labels": "x=y a=b",
            "annotations": "x",
        }
        err = "Invalid format 'x'. Expected format key=value."
        with self.assertRaises(ValueError) as cm:
            ns.aks_managed_namespace_add(cmd, None, raw_parameters, None, False)
        self.assertEqual(str(cm.exception), err)

    def test_add_managed_namespace_with_missing_cpu_request(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "cpu_limit": "300m",
        }
        err = "Please specify --cpu-request, --cpu-limit, --memory-request, and --memory-limit."
        with self.assertRaises(RequiredArgumentMissingError) as cm:
            ns.aks_managed_namespace_add(cmd, None, raw_parameters, None, False)
        self.assertEqual(str(cm.exception), err)
    
    def test_add_managed_namespace_with_invalid_ingress_policy(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "cpu_request": "300m",
            "cpu_limit": "500m",
            "memory_request": "1Gi",
            "memory_limit": "2Gi",
            "ingress_policy": "deny",
        }
        err = "Invalid ingress_policy 'deny'"
        with self.assertRaises(InvalidArgumentValueError) as cm:
            ns.aks_managed_namespace_add(cmd, None, raw_parameters, None, False)
        self.assertIn(err, str(cm.exception))

    def test_add_managed_namespace_with_invalid_egress_policy(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "cpu_request": "300m",
            "cpu_limit": "500m",
            "memory_request": "1Gi",
            "memory_limit": "2Gi",
            "ingress_policy": "DenyAll",
            "egress_policy": "deny",
        }
        err = "Invalid egress_policy 'deny'"
        with self.assertRaises(InvalidArgumentValueError) as cm:
            ns.aks_managed_namespace_add(cmd, None, raw_parameters, None, False)
        self.assertIn(err, str(cm.exception))
        
    def test_add_managed_namespace_with_invalid_adoption_policy(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "cpu_request": "300m",
            "cpu_limit": "500m",
            "memory_request": "1Gi",
            "memory_limit": "2Gi",
            "ingress_policy": "DenyAll",
            "egress_policy": "AllowAll",
            "adoption_policy": "abc",
        }
        err = "Invalid adoption policy 'abc'"
        with self.assertRaises(InvalidArgumentValueError) as cm:
            ns.aks_managed_namespace_add(cmd, None, raw_parameters, None, False)
        self.assertIn(err, str(cm.exception))

    def test_add_managed_namespace_with_invalid_delete_policy(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "cpu_request": "300m",
            "cpu_limit": "500m",
            "memory_request": "1Gi",
            "memory_limit": "2Gi",
            "ingress_policy": "DenyAll",
            "egress_policy": "AllowAll",
            "adoption_policy": "Always",
            "delete_policy": "abc",
        }
        err = "Invalid delete policy 'abc'"
        with self.assertRaises(InvalidArgumentValueError) as cm:
            ns.aks_managed_namespace_add(cmd, None, raw_parameters, None, False)
        self.assertIn(err, str(cm.exception))

    # aks_managed_namespace_add(cmd, client, raw_parameters, headers, no_wait):
    # aks_managed_namespace_update(cmd, client, raw_parameters, headers, existedNamespace, no_wait)


@patch("azure.cli.command_modules.acs.managednamespace.get_container_service_client")
class TestUpdateManagedNamespace(unittest.TestCase):
    def setUp(self):
        # Set up mock cluster client and location
        self.mock_cluster = Mock()
        self.mock_cluster.location = "eastus"

        self.mock_managed_clusters = Mock()
        self.mock_managed_clusters.get.return_value = self.mock_cluster

        self.mock_client = Mock()
        self.mock_client.managed_clusters = self.mock_managed_clusters


    def test_update_managed_namespace_with_invalid_ingress_policy(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "cpu_request": "300m",
            "cpu_limit": "500m",
            "memory_request": "1Gi",
            "memory_limit": "2Gi",
            "ingress_policy": "deny",
        }
        err = "Invalid ingress_policy 'deny'"
        with self.assertRaises(InvalidArgumentValueError) as cm:
            ns.aks_managed_namespace_update(cmd, None, raw_parameters, None, None, False)
        self.assertIn(err, str(cm.exception))

    def test_update_managed_namespace_with_invalid_egress_policy(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "cpu_request": "300m",
            "cpu_limit": "500m",
            "memory_request": "1Gi",
            "memory_limit": "2Gi",
            "ingress_policy": "DenyAll",
            "egress_policy": "deny",
        }
        err = "Invalid egress_policy 'deny'"
        with self.assertRaises(InvalidArgumentValueError) as cm:
            ns.aks_managed_namespace_update(cmd, None, raw_parameters, None, None, False)
        self.assertIn(err, str(cm.exception))
        
    def test_update_managed_namespace_with_invalid_adoption_policy(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "cpu_request": "300m",
            "cpu_limit": "500m",
            "memory_request": "1Gi",
            "memory_limit": "2Gi",
            "ingress_policy": "DenyAll",
            "egress_policy": "AllowAll",
            "adoption_policy": "abc",
        }
        err = "Invalid adoption policy 'abc'"
        with self.assertRaises(InvalidArgumentValueError) as cm:
            ns.aks_managed_namespace_update(cmd, None, raw_parameters, None, None, False)
        self.assertIn(err, str(cm.exception))

    def test_update_managed_namespace_with_invalid_delete_policy(self, mock_get_client):
        cli_ctx = MockCLI()
        cmd = MockCmd(cli_ctx)

        mock_get_client.return_value = self.mock_client

        raw_parameters = {
            "resource_group_name": "test_rg",
            "cluster_name": "test_cluster",
            "name": "test_managed_namespace",
            "cpu_request": "300m",
            "cpu_limit": "500m",
            "memory_request": "1Gi",
            "memory_limit": "2Gi",
            "ingress_policy": "DenyAll",
            "egress_policy": "AllowAll",
            "adoption_policy": "Always",
            "delete_policy": "abc",
        }
        err = "Invalid delete policy 'abc'"
        with self.assertRaises(InvalidArgumentValueError) as cm:
            ns.aks_managed_namespace_update(cmd, None, raw_parameters, None, None, False)
        self.assertIn(err, str(cm.exception))


if __name__ == "__main__":
    unittest.main()
