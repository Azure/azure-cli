# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from uuid import uuid4

from azure.cli.command_modules.resource._utils import split_resource_id


class TestSplitResourceId(unittest.TestCase):
    def test_subscription_level_id(self):
        subscription_id = uuid4()
        role_assignment_id = uuid4()

        scope, relative_resource_id = split_resource_id(
            f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleAssignment/{role_assignment_id}"
        )

        self.assertEqual(scope, f"/subscriptions/{subscription_id}")
        self.assertEqual(relative_resource_id, f"Microsoft.Authorization/roleAssignment/{role_assignment_id}")

    def test_resource_group_level_id(self):
        subscription_id = uuid4()

        scope, relative_resource_id = split_resource_id(
            f"/subscriptions/{subscription_id}/resourceGroups/test-what-if-rg/providers/Microsoft.Sql/servers/dbserver"
        )

        self.assertEqual(scope, f"/subscriptions/{subscription_id}/resourceGroups/test-what-if-rg")
        self.assertEqual(relative_resource_id, "Microsoft.Sql/servers/dbserver")

    def test_resource_group_id(self):
        subscription_id = uuid4()

        scope, relative_resource_id = split_resource_id(
            f"/subscriptions/{subscription_id}/resourceGroups/test-what-if-rg"
        )

        self.assertEqual(scope, f"/subscriptions/{subscription_id}")
        self.assertEqual(relative_resource_id, "resourceGroups/test-what-if-rg")

    def test_management_group_level_id(self):
        role_assignment_id = uuid4()

        scope, relative_resource_id = split_resource_id(
            f"/providers/Microsoft.Management/ManagementGroups/myManagementGroup/providers/Microsoft.Authorization/roleAssignments/{role_assignment_id}"
        )

        self.assertEqual(scope, "/providers/Microsoft.Management/ManagementGroups/myManagementGroup")
        self.assertEqual(relative_resource_id, f"Microsoft.Authorization/roleAssignments/{role_assignment_id}")

    def test_management_group_id(self):
        scope, relative_resource_id = split_resource_id(
            "/providers/Microsoft.Management/ManagementGroups/myManagementGroup"
        )

        self.assertEqual(scope, "/")
        self.assertEqual(relative_resource_id, "Microsoft.Management/ManagementGroups/myManagementGroup")

    def test_tenant_level_id(self):
        role_assignment_id = uuid4()

        scope, relative_resource_id = split_resource_id(
            f"/providers/Microsoft.Authorization/roleAssignments/{role_assignment_id}"
        )

        self.assertEqual(scope, "/")
        self.assertEqual(relative_resource_id, f"Microsoft.Authorization/roleAssignments/{role_assignment_id}")
