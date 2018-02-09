# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only

@record_only()
class AzureManagementGroupsScenarioTest(ScenarioTest):
    def test_list_managementgroups(self):
        managementgroups_list = self.cmd('managementgroups group list').get_output_in_json()
        self.assertIsNotNone(managementgroups_list)
        self.assertTrue(len(managementgroups_list)>0)
        self.assertIsNotNone(managementgroups_list[0]["displayName"])
        self.assertTrue(managementgroups_list[0]["id"].startswith("/providers/Microsoft.Management/managementGroups/"))
        self.assertIsNotNone(managementgroups_list[0]["name"])
        self.assertIsNotNone(managementgroups_list[0]["tenantId"])
        self.assertEqual(managementgroups_list[0]["type"], "/providers/Microsoft.Management/managementGroups")

    def test_get_managementgroup(self):
        managementgroup_get = self.cmd('managementgroups group get --group-name testGroup123').get_output_in_json()
        self.assertIsNotNone(managementgroup_get)
        self.assertIsNone(managementgroup_get["children"])
        self.assertIsNotNone(managementgroup_get["details"])
        self.assertIsNotNone(managementgroup_get["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_get["details"]["parent"]["parentId"])
        self.assertTrue(managementgroup_get["details"]["parent"]["parentId"].startswith("/providers/Microsoft.Management/managementGroups/"))
        self.assertIsNotNone(managementgroup_get["displayName"])
        self.assertIsNotNone(managementgroup_get["name"])
        self.assertIsNotNone(managementgroup_get["tenantId"])
        self.assertEqual(managementgroup_get["type"], "/providers/Microsoft.Management/managementGroups")

    def test_get_managementgroup_with_expand(self):
        managementgroup_get = self.cmd('managementgroups group get --group-name testGroup123 --expand').get_output_in_json()
        self.assertIsNotNone(managementgroup_get)
        self.assertIsNotNone(managementgroup_get["details"])
        self.assertIsNotNone(managementgroup_get["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_get["details"]["parent"]["parentId"])
        self.assertTrue(managementgroup_get["details"]["parent"]["parentId"].startswith("/providers/Microsoft.Management/managementGroups/"))
        self.assertIsNotNone(managementgroup_get["displayName"])
        self.assertIsNotNone(managementgroup_get["name"])
        self.assertIsNotNone(managementgroup_get["tenantId"])
        self.assertEqual(managementgroup_get["type"], "/providers/Microsoft.Management/managementGroups")
        self.assertIsNotNone(managementgroup_get["children"])
        self.assertIsNotNone(managementgroup_get["children"][0]["childId"])
        self.assertIsNotNone(managementgroup_get["children"][0]["childType"])
        self.assertIsNotNone(managementgroup_get["children"][0]["displayName"])
        self.assertIsNone(managementgroup_get["children"][0]["children"])


    def test_get_managementgroup_with_expand_and_recurse(self):
        managementgroup_get = self.cmd('managementgroups group get --group-name testGroup123 --expand --recurse').get_output_in_json()
        self.assertIsNotNone(managementgroup_get)
        self.assertIsNotNone(managementgroup_get["details"])
        self.assertIsNotNone(managementgroup_get["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_get["details"]["parent"]["parentId"])
        self.assertTrue(managementgroup_get["details"]["parent"]["parentId"].startswith("/providers/Microsoft.Management/managementGroups/"))
        self.assertIsNotNone(managementgroup_get["displayName"])
        self.assertIsNotNone(managementgroup_get["name"])
        self.assertIsNotNone(managementgroup_get["tenantId"])
        self.assertEqual(managementgroup_get["type"], "/providers/Microsoft.Management/managementGroups")
        self.assertIsNotNone(managementgroup_get["children"])
        self.assertIsNotNone(managementgroup_get["children"][0]["childId"])
        self.assertIsNotNone(managementgroup_get["children"][0]["childType"])
        self.assertIsNotNone(managementgroup_get["children"][0]["displayName"])
        self.assertIsNotNone(managementgroup_get["children"][0]["children"][0]["childId"])
        self.assertIsNotNone(managementgroup_get["children"][0]["children"][0]["childType"])
        self.assertIsNotNone(managementgroup_get["children"][0]["children"][0]["displayName"])

    def test_new_managementgroup(self):
        name = "testcligroup"
        displayName = "testcligroup"
        managementgroup_create = self.cmd('managementgroups group new --group-name '+name).get_output_in_json()
        self.assertIsNone(managementgroup_create["children"])
        self.assertIsNotNone(managementgroup_create["details"])
        self.assertIsNotNone(managementgroup_create["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_create["details"]["parent"]["parentId"])
        self.assertTrue(managementgroup_create["details"]["parent"]["parentId"].startswith("/providers/Microsoft.Management/managementGroups/"))
        self.assertEqual(managementgroup_create["displayName"], displayName)
        self.assertEqual(managementgroup_create["name"], name)
        self.assertIsNotNone(managementgroup_create["tenantId"])
        self.assertEqual(managementgroup_create["type"], "/providers/Microsoft.Management/managementGroups")

    def test_new_managementgroup_with_displayname(self):
        name = "testcligroup1"
        displayName = "TestCliDisplayName"
        managementgroup_create = self.cmd('managementgroups group new --group-name '+name+' --display-name '+displayName).get_output_in_json()
        self.assertIsNone(managementgroup_create["children"])
        self.assertIsNotNone(managementgroup_create["details"])
        self.assertIsNotNone(managementgroup_create["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_create["details"]["parent"]["parentId"])
        self.assertTrue(managementgroup_create["details"]["parent"]["parentId"].startswith("/providers/Microsoft.Management/managementGroups/"))
        self.assertEqual(managementgroup_create["displayName"], displayName)
        self.assertEqual(managementgroup_create["name"], name)
        self.assertIsNotNone(managementgroup_create["tenantId"])
        self.assertEqual(managementgroup_create["type"], "/providers/Microsoft.Management/managementGroups")

    def test_new_managementgroup_with_parentid(self):
        name = "testcligroupchild"
        displayName = "testcligroupchild"
        parentId = "/providers/Microsoft.Management/managementGroups/testcligroup"
        managementgroup_create = self.cmd('managementgroups group new --group-name '+name+' --parent-id '+parentId).get_output_in_json()
        self.assertIsNone(managementgroup_create["children"])
        self.assertIsNotNone(managementgroup_create["details"])
        self.assertIsNotNone(managementgroup_create["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_create["details"]["parent"]["parentId"])
        self.assertEqual(managementgroup_create["details"]["parent"]["parentId"], parentId)
        self.assertEqual(managementgroup_create["displayName"], displayName)
        self.assertEqual(managementgroup_create["name"], name)
        self.assertIsNotNone(managementgroup_create["tenantId"])
        self.assertEqual(managementgroup_create["type"], "/providers/Microsoft.Management/managementGroups")

    def test_new_managementgroup_with_displayname_and_parentid(self):
        name = "testcligroupchild2"
        displayName = "TestCliGroupChild2Display"
        parentId = "/providers/Microsoft.Management/managementGroups/testcligroup"
        managementgroup_create = self.cmd('managementgroups group new --group-name '+name+' --display-name '+displayName+' --parent-id '+parentId).get_output_in_json()
        self.assertIsNone(managementgroup_create["children"])
        self.assertIsNotNone(managementgroup_create["details"])
        self.assertIsNotNone(managementgroup_create["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_create["details"]["parent"]["parentId"])
        self.assertEqual(managementgroup_create["details"]["parent"]["parentId"], parentId)
        self.assertEqual(managementgroup_create["displayName"], displayName)
        self.assertEqual(managementgroup_create["name"], name)
        self.assertIsNotNone(managementgroup_create["tenantId"])
        self.assertEqual(managementgroup_create["type"], "/providers/Microsoft.Management/managementGroups")

    def test_update_managementgroup_with_displayname(self):
        name = "testcligroup1"
        displayName = "TestCliDisplayNameUpdate"
        managementgroup_update = self.cmd('managementgroups group update --group-name '+name+' --display-name '+displayName).get_output_in_json()
        self.assertIsNone(managementgroup_update["children"])
        self.assertIsNotNone(managementgroup_update["details"])
        self.assertIsNotNone(managementgroup_update["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_update["details"]["parent"]["parentId"])
        self.assertTrue(managementgroup_update["details"]["parent"]["parentId"].startswith("/providers/Microsoft.Management/managementGroups/"))
        self.assertEqual(managementgroup_update["displayName"], displayName)
        self.assertEqual(managementgroup_update["name"], name)
        self.assertIsNotNone(managementgroup_update["tenantId"])
        self.assertEqual(managementgroup_update["type"], "/providers/Microsoft.Management/managementGroups")

    def test_update_managementgroup_with_parentid(self):
        name = "testcligroupchild"
        displayName = "testcligroupchild"
        parentId = "/providers/Microsoft.Management/managementGroups/testcligroup1"
        managementgroup_update = self.cmd('managementgroups group update --group-name '+name+' --parent-id '+parentId).get_output_in_json()
        self.assertIsNone(managementgroup_update["children"])
        self.assertIsNotNone(managementgroup_update["details"])
        self.assertIsNotNone(managementgroup_update["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_update["details"]["parent"]["parentId"])
        self.assertEqual(managementgroup_update["details"]["parent"]["parentId"], parentId)
        self.assertEqual(managementgroup_update["displayName"], displayName)
        self.assertEqual(managementgroup_update["name"], name)
        self.assertIsNotNone(managementgroup_update["tenantId"])
        self.assertEqual(managementgroup_update["type"], "/providers/Microsoft.Management/managementGroups")

    def test_update_managementgroup_with_displayname_and_parentid(self):
        name = "testcligroupchild2"
        displayName = "TestCliGroupChild2DisplayUpdate"
        parentId = "/providers/Microsoft.Management/managementGroups/testcligroup1"
        managementgroup_update = self.cmd('managementgroups group update --group-name '+name+' --display-name '+displayName+' --parent-id '+parentId).get_output_in_json()
        self.assertIsNone(managementgroup_update["children"])
        self.assertIsNotNone(managementgroup_update["details"])
        self.assertIsNotNone(managementgroup_update["details"]["parent"]["displayName"])
        self.assertIsNotNone(managementgroup_update["details"]["parent"]["parentId"])
        self.assertEqual(managementgroup_update["details"]["parent"]["parentId"], parentId)
        self.assertEqual(managementgroup_update["displayName"], displayName)
        self.assertEqual(managementgroup_update["name"], name)
        self.assertIsNotNone(managementgroup_update["tenantId"])
        self.assertEqual(managementgroup_update["type"], "/providers/Microsoft.Management/managementGroups")

    def test_new_remove_subscription_managementgroup(self):
        self.cmd('managementgroups subscription new --group-name testGroup123 --subscription-id 2a418b54-7643-4d8f-982c-d0802205d12c')
        self.cmd('managementgroups subscription remove --group-name testGroup123 --subscription-id 2a418b54-7643-4d8f-982c-d0802205d12c')

    def test_new_remove_group_managementgroup(self):
        self.cmd('managementgroups group new --group-name testclirandgroup')
        self.cmd('managementgroups group remove --group-name testclirandgroup')
