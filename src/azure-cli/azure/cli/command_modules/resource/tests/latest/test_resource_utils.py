# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from uuid import uuid4

from azure.cli.command_modules.resource._utils import parse_resource_id


class TestParseResourceId(unittest.TestCase):
    def test_subscription_level_id(self):
        subscription_id = uuid4()
        role_assignment_id = uuid4()

        scope, relative_resource_id = parse_resource_id(
            f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleAssignment/{role_assignment_id}"
        )

        self.assertEqual(scope, f"/subscriptions/{subscription_id}")
        self.assertEqual(relative_resource_id, f"Microsoft.Authorization/roleAssignment/{role_assignment_id}")

    def test_resource_group_level_id(self):
        subscription_id = uuid4()

        scope, relative_resource_id = parse_resource_id(
            f"/subscriptions/{subscription_id}/resourceGroups/test-what-if-rg/providers/Microsoft.Sql/servers/dbserver"
        )

        self.assertEqual(scope, f"/subscriptions/{subscription_id}/resourceGroups/test-what-if-rg")
        self.assertEqual(relative_resource_id, "Microsoft.Sql/servers/dbserver")

    def test_resource_group_id(self):
        subscription_id = uuid4()

        scope, relative_resource_id = parse_resource_id(
            f"/subscriptions/{subscription_id}/resourceGroups/test-what-if-rg"
        )

        self.assertEqual(scope, f"/subscriptions/{subscription_id}")
        self.assertEqual(relative_resource_id, "resourceGroups/test-what-if-rg")
