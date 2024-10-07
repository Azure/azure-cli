# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.core.aaz import AAZIdentityObjectType
from azure.cli.core.aaz._field_value import AAZIdentityObject


class TestAAZIdentity(unittest.TestCase):
    identity = AAZIdentityObject(schema=AAZIdentityObjectType(), data={})

    def test_main_command(self):
        result = {}
        data = {
            "userAssigned": ["a", "b"],
            "systemAssigned": "SystemAssigned",
            "action": "create",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result["type"] == "SystemAssigned,UserAssigned")
        self.assertTrue(result["userAssignedIdentities"] == {"a": {}, "b": {}})

        result = {}
        data = {
            "userAssigned": [],
            "systemAssigned": "SystemAssigned",
            "action": "create",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result["type"] == "SystemAssigned")
        self.assertTrue("userAssignedIdentities" not in result)

        result = {}
        data = {
            "userAssigned": [],
            "action": "create",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result == {})

        result = {}
        data = {"action": "create"}
        result = self.identity._build_identity(data, result)
        self.assertTrue(result == {})

    def test_assign_command(self):
        result = {
            "type": "systemAssigned, userAssigned",
            "userAssignedIdentities": {"a": {}, "b": {}},
        }
        data = {
            "userAssigned": ["b", "c"],
            "action": "assign",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result["type"] == "SystemAssigned,UserAssigned")
        self.assertTrue(result["userAssignedIdentities"] == {"a": {}, "b": {}, "c": {}})

        result = {
            "type": "userAssigned",
            "userAssignedIdentities": {"a": {}, "b": {}},
        }
        data = {
            "systemAssigned": "SystemAssigned",
            "action": "assign",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result["type"] == "SystemAssigned,UserAssigned")
        self.assertTrue(result["userAssignedIdentities"] == {"a": {}, "b": {}})

        result = {
            "type": "systemAssigned",
        }
        data = {
            "userAssigned": ["a", "b"],
            "action": "assign",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result["type"] == "SystemAssigned,UserAssigned")
        self.assertTrue(result["userAssignedIdentities"] == {"a": {}, "b": {}})

        result = {}
        data = {
            "userAssigned": ["a", "b"],
            "action": "assign",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result["type"] == "UserAssigned")
        self.assertTrue(result["userAssignedIdentities"] == {"a": {}, "b": {}})

        result = {}
        data = {
            "userAssigned": [],
            "action": "assign",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result == {})

    def test_remove_command(self):
        result = {
            "type": "systemAssigned, userAssigned",
            "userAssignedIdentities": {"a": {}, "b": {}},
        }
        data = {
            "userAssigned": ["b", "c"],
            "systemAssigned": "SystemAssigned",
            "action": "remove",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result["type"] == "UserAssigned")
        self.assertTrue(result["userAssignedIdentities"] == {"a": {}})

        result = {
            "type": "systemAssigned, userAssigned",
            "userAssignedIdentities": {"a": {}, "b": {}},
        }
        data = {
            "userAssigned": [],
            "action": "remove",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result["type"] == "SystemAssigned")
        self.assertTrue("userAssignedIdentities" not in result)

        result = {
            "type": "userAssigned",
            "userAssignedIdentities": {"a": {}, "b": {}},
        }
        data = {
            "userAssigned": [],
            "action": "remove",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result == {})

        result = {}
        data = {
            "userAssigned": ["a", "b"],
            "action": "remove",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result == {})

        result = {}
        data = {
            "userAssigned": [],
            "action": "remove",
        }
        result = self.identity._build_identity(data, result)
        self.assertTrue(result == {})
