# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only
import pytest

@pytest.mark.custom_mark
class AzureManagementGroupsScenarioTest(ScenarioTest):
    
    #@pytest.mark.custom_mark
    def test_list_managementgroups(self):
        managementgroups_list = self.cmd(
            'account management-group list').get_output_in_json()
        self.assertIsNotNone(managementgroups_list)
        self.assertTrue(len(managementgroups_list) > 0)
        self.assertIsNotNone(managementgroups_list[0]["displayName"])
        self.assertTrue(managementgroups_list[0]["id"].startswith(
            "/providers/Microsoft.Management/managementGroups/"))
        self.assertIsNotNone(managementgroups_list[0]["name"])
        self.assertIsNotNone(managementgroups_list[0]["tenantId"])
        self.assertEqual(
            managementgroups_list[0]["type"],
            "Microsoft.Management/managementGroups")

    #@pytest.mark.custom_mark1
    def test_show_managementgroup(self):
        self.cmd('account management-group create --name testcligetgroup')
        self.cmd('account management-group create --name testcligetgroup1 --parent /providers/Microsoft.Management/managementGroups/testcligetgroup')
        managementgroup_get = self.cmd(
            'account management-group show --name testcligetgroup1').get_output_in_json()
        self.cmd('account management-group delete --name testcligetgroup1')
        self.cmd('account management-group delete --name testcligetgroup')

        self.assertIsNotNone(managementgroup_get)
        self.assertIsNone(managementgroup_get["children"])
        self.assertIsNotNone(managementgroup_get["details"])
        self.assertEqual(
            managementgroup_get["id"],
            "/providers/Microsoft.Management/managementGroups/testcligetgroup1")
        self.assertEqual(managementgroup_get["name"], "testcligetgroup1")
        self.assertEqual(
            managementgroup_get["displayName"],
            "testcligetgroup1")
        self.assertEqual(
            managementgroup_get["details"]["parent"]["displayName"],
            "testcligetgroup")
        self.assertEqual(
            managementgroup_get["details"]["parent"]["id"],
            "/providers/Microsoft.Management/managementGroups/testcligetgroup")
        self.assertEqual(
            managementgroup_get["details"]["parent"]["name"],
            "testcligetgroup")
        self.assertIsNotNone(managementgroup_get["tenantId"])
        self.assertEqual(
            managementgroup_get["type"],
            "Microsoft.Management/managementGroups")

    #@pytest.mark.custom_mark1
    def test_show_managementgroup_with_expand(self):
        self.cmd('account management-group create --name testcligetgroup')
        self.cmd('account management-group create --name testcligetgroup1 --parent testcligetgroup')
        self.cmd('account management-group create --name testcligetgroup2 --parent /providers/Microsoft.Management/managementGroups/testcligetgroup1')
        managementgroup_get = self.cmd(
            'account management-group show --name testcligetgroup1 --expand').get_output_in_json()
        self.cmd('account management-group delete --name testcligetgroup2')
        self.cmd('account management-group delete --name testcligetgroup1')
        self.cmd('account management-group delete --name testcligetgroup')

        self.assertIsNotNone(managementgroup_get)
        self.assertIsNotNone(managementgroup_get["children"])
        self.assertIsNotNone(managementgroup_get["details"])
        self.assertEqual(
            managementgroup_get["id"],
            "/providers/Microsoft.Management/managementGroups/testcligetgroup1")
        self.assertEqual(managementgroup_get["name"], "testcligetgroup1")
        self.assertEqual(
            managementgroup_get["displayName"],
            "testcligetgroup1")
        self.assertEqual(
            managementgroup_get["details"]["parent"]["displayName"],
            "testcligetgroup")
        self.assertEqual(
            managementgroup_get["details"]["parent"]["id"],
            "/providers/Microsoft.Management/managementGroups/testcligetgroup")
        self.assertEqual(
            managementgroup_get["details"]["parent"]["name"],
            "testcligetgroup")
        self.assertIsNotNone(managementgroup_get["tenantId"])
        self.assertEqual(
            managementgroup_get["type"],
            "Microsoft.Management/managementGroups")
        self.assertEqual(
            managementgroup_get["children"][0]["id"],
            "/providers/Microsoft.Management/managementGroups/testcligetgroup2")
        self.assertEqual(
            managementgroup_get["children"][0]["type"],
            "Microsoft.Management/managementGroups")
        self.assertEqual(
            managementgroup_get["children"][0]["displayName"],
            "testcligetgroup2")
        self.assertEqual(
            managementgroup_get["children"][0]["name"],
            "testcligetgroup2")

    #@pytest.mark.custom_mark1
    def test_show_managementgroup_with_expand_and_recurse(self):
        self.cmd('account management-group create --name testcligetgroup1')
        self.cmd('account management-group create --name testcligetgroup2 --parent /providers/Microsoft.Management/managementGroups/testcligetgroup1')
        self.cmd('account management-group create --name testcligetgroup3 --parent testcligetgroup2')
        self.cmd('account management-group create --name testcligetgroup4 --parent /providers/Microsoft.Management/managementGroups/testcligetgroup3')
        managementgroup_get = self.cmd(
            'account management-group show --name testcligetgroup2 --expand --recurse').get_output_in_json()
        self.cmd('account management-group delete --name testcligetgroup4')
        self.cmd('account management-group delete --name testcligetgroup3')
        self.cmd('account management-group delete --name testcligetgroup2')
        self.cmd('account management-group delete --name testcligetgroup1')

        self.assertIsNotNone(managementgroup_get)
        self.assertIsNotNone(managementgroup_get["children"])
        self.assertIsNotNone(managementgroup_get["details"])
        self.assertEqual(
            managementgroup_get["id"],
            "/providers/Microsoft.Management/managementGroups/testcligetgroup2")
        self.assertEqual(managementgroup_get["name"], "testcligetgroup2")
        self.assertEqual(
            managementgroup_get["displayName"],
            "testcligetgroup2")
        self.assertEqual(
            managementgroup_get["details"]["parent"]["displayName"],
            "testcligetgroup1")
        self.assertEqual(
            managementgroup_get["details"]["parent"]["id"],
            "/providers/Microsoft.Management/managementGroups/testcligetgroup1")
        self.assertEqual(
            managementgroup_get["details"]["parent"]["name"],
            "testcligetgroup1")
        self.assertIsNotNone(managementgroup_get["tenantId"])
        self.assertEqual(
            managementgroup_get["type"],
            "Microsoft.Management/managementGroups")
        self.assertEqual(
            managementgroup_get["children"][0]["id"],
            "/providers/Microsoft.Management/managementGroups/testcligetgroup3")
        self.assertEqual(
            managementgroup_get["children"][0]["type"],
            "Microsoft.Management/managementGroups")
        self.assertEqual(
            managementgroup_get["children"][0]["displayName"],
            "testcligetgroup3")
        self.assertEqual(
            managementgroup_get["children"][0]["name"],
            "testcligetgroup3")
        self.assertEqual(
            managementgroup_get["children"][0]["children"][0]["id"],
            "/providers/Microsoft.Management/managementGroups/testcligetgroup4")
        self.assertEqual(
            managementgroup_get["children"][0]["children"][0]["type"],
            "Microsoft.Management/managementGroups")
        self.assertEqual(
            managementgroup_get["children"][0]["children"][0]["displayName"],
            "testcligetgroup4")
        self.assertEqual(
            managementgroup_get["children"][0]["children"][0]["name"],
            "testcligetgroup4")
    
    #@pytest.mark.custom_mark1
    def test_create_managementgroup(self):
        name = "testcligroup"
        displayName = "testcligroup"
        managementgroup_create = self.cmd(
            'account management-group create --name ' +
            name).get_output_in_json()
        self.cmd('account management-group delete --name ' + name)

        self.assertIsNotNone(managementgroup_create)
        self.assertIsNotNone(managementgroup_create["details"])
        self.assertEqual(
            managementgroup_create["id"],
            "/providers/Microsoft.Management/managementGroups/" + name)
        self.assertEqual(managementgroup_create["name"], name)
        self.assertEqual(
            managementgroup_create["displayName"],
            displayName)
        self.assertEqual(
            managementgroup_create["details"]["parent"]["displayName"],
            "Root Management Group")
        self.assertEqual(
            managementgroup_create["details"]["parent"]["id"],
            "/providers/Microsoft.Management/managementGroups/" +
            managementgroup_create["tenantId"])
        self.assertEqual(
            managementgroup_create["details"]["parent"]["name"],
            managementgroup_create["tenantId"])
        self.assertIsNotNone(managementgroup_create["tenantId"])
        self.assertEqual(
            managementgroup_create["type"],
            "Microsoft.Management/managementGroups")

    #@pytest.mark.custom_mark1
    def test_create_managementgroup_with_displayname(self):
        name = "testcligroup"
        displayName = "TestCliDisplayName"
        managementgroup_create = self.cmd(
            'account management-group create --name ' +
            name +
            ' --display-name ' +
            displayName).get_output_in_json()
        self.cmd('account management-group delete --name ' + name)

        self.assertIsNotNone(managementgroup_create)
        self.assertIsNotNone(managementgroup_create["details"])
        self.assertEqual(
            managementgroup_create["id"],
            "/providers/Microsoft.Management/managementGroups/" + name)
        self.assertEqual(managementgroup_create["name"], name)
        self.assertEqual(
            managementgroup_create["displayName"],
            displayName)
        self.assertEqual(
            managementgroup_create["details"]["parent"]["displayName"],
            "Root Management Group")
        self.assertEqual(
            managementgroup_create["details"]["parent"]["id"],
            "/providers/Microsoft.Management/managementGroups/" +
            managementgroup_create["tenantId"])
        self.assertEqual(
            managementgroup_create["details"]["parent"]["name"],
            managementgroup_create["tenantId"])
        self.assertIsNotNone(managementgroup_create["tenantId"])
        self.assertEqual(
            managementgroup_create["type"],
            "Microsoft.Management/managementGroups")

    #@pytest.mark.custom_mark
    def test_create_managementgroup_with_parentid(self):
        name = "testcligroupchild"
        displayName = "testcligroupchild"
        parentId = "/providers/Microsoft.Management/managementGroups/testcligroup"
        parentName = "testcligroup"
        self.cmd('account management-group create --name ' + parentName)
        managementgroup_create = self.cmd(
            'account management-group create --name ' +
            name +
            ' --parent ' +
            parentId).get_output_in_json()
        self.cmd('account management-group delete --name ' + name)
        self.cmd('account management-group delete --name ' + parentName)

        self.assertIsNotNone(managementgroup_create)
        self.assertIsNotNone(managementgroup_create["details"])
        self.assertEqual(
            managementgroup_create["id"],
            "/providers/Microsoft.Management/managementGroups/" + name)
        self.assertEqual(managementgroup_create["name"], name)
        self.assertEqual(
            managementgroup_create["displayName"],
            displayName)
        self.assertEqual(
            managementgroup_create["details"]["parent"]["displayName"],
            parentName)
        self.assertEqual(
            managementgroup_create["details"]["parent"]["id"],
            parentId)
        self.assertEqual(
            managementgroup_create["details"]["parent"]["name"],
            parentName)
        self.assertIsNotNone(managementgroup_create["tenantId"])
        self.assertEqual(
            managementgroup_create["type"],
            "Microsoft.Management/managementGroups")

    #@pytest.mark.custom_mark1
    def test_create_managementgroup_with_displayname_and_parentid(self):
        name = "testcligroupchild"
        displayName = "testcligroupchildDisplayName"
        parentId = "/providers/Microsoft.Management/managementGroups/testcligroup"
        parentName = "testcligroup"
        self.cmd('account management-group create --name ' + parentName)
        managementgroup_create = self.cmd(
            'account management-group create --name ' +
            name +
            ' --display-name ' +
            displayName +
            ' --parent ' +
            parentName).get_output_in_json()
        self.cmd('account management-group delete --name ' + name)
        self.cmd('account management-group delete --name ' + parentName)

        self.assertIsNotNone(managementgroup_create)
        self.assertIsNotNone(managementgroup_create["details"])
        self.assertEqual(
            managementgroup_create["id"],
            "/providers/Microsoft.Management/managementGroups/" + name)
        self.assertEqual(managementgroup_create["name"], name)
        self.assertEqual(
            managementgroup_create["displayName"],
            displayName)
        self.assertEqual(
            managementgroup_create["details"]["parent"]["displayName"],
            parentName)
        self.assertEqual(
            managementgroup_create["details"]["parent"]["id"],
            parentId)
        self.assertEqual(
            managementgroup_create["details"]["parent"]["name"],
            parentName)
        self.assertIsNotNone(managementgroup_create["tenantId"])
        self.assertEqual(
            managementgroup_create["type"],
            "Microsoft.Management/managementGroups")

    #@pytest.mark.custom_mark
    def test_update_managementgroup_with_displayname(self):
        name = "testcligroup"
        displayName = "testcligroupDisplayName"
        self.cmd('account management-group create --name ' + name)
        managementgroup_update = self.cmd(
            'account management-group update --name ' +
            name +
            ' --display-name ' +
            displayName).get_output_in_json()
        self.cmd('account management-group delete --name ' + name)

        self.assertIsNotNone(managementgroup_update)
        self.assertIsNotNone(managementgroup_update["details"])
        self.assertEqual(
            managementgroup_update["id"],
            "/providers/Microsoft.Management/managementGroups/" + name)
        self.assertEqual(managementgroup_update["name"], name)
        self.assertEqual(managementgroup_update["displayName"], displayName)
        self.assertEqual(
            managementgroup_update["details"]["parent"]["displayName"],
            "Root Management Group")
        self.assertEqual(
            managementgroup_update["details"]["parent"]["id"],
            "/providers/Microsoft.Management/managementGroups/" +
            managementgroup_update["tenantId"])
        self.assertEqual(
            managementgroup_update["details"]["parent"]["name"],
            managementgroup_update["tenantId"])
        self.assertIsNotNone(managementgroup_update["tenantId"])
        self.assertEqual(
            managementgroup_update["type"],
            "Microsoft.Management/managementGroups")

    #@pytest.mark.custom_mark1
    def test_update_managementgroup_with_parentid(self):
        name = "testcligroupchild"
        displayName = "testcligroupchild"
        parentId = "/providers/Microsoft.Management/managementGroups/testcligroup"
        parentName = "testcligroup"
        self.cmd('account management-group create --name ' + parentName)
        self.cmd('account management-group create --name ' + name)
        managementgroup_update = self.cmd(
            'account management-group update --name ' +
            name +
            ' --parent ' +
            parentId).get_output_in_json()
        print(managementgroup_update)
        self.cmd('account management-group delete --name ' + name)
        self.cmd('account management-group delete --name ' + parentName)

        self.assertIsNotNone(managementgroup_update)
        self.assertIsNotNone(managementgroup_update["details"])
        self.assertEqual(
            managementgroup_update["id"],
            "/providers/Microsoft.Management/managementGroups/" + name)
        self.assertEqual(managementgroup_update["name"], name)
        self.assertEqual(managementgroup_update["displayName"], displayName)
        self.assertEqual(
            managementgroup_update["details"]["parent"]["displayName"],
            parentName)
        self.assertEqual(
            managementgroup_update["details"]["parent"]["id"],
            parentId)
        self.assertEqual(
            managementgroup_update["details"]["parent"]["name"],
            parentName)
        self.assertIsNotNone(managementgroup_update["tenantId"])
        self.assertEqual(
            managementgroup_update["type"],
            "Microsoft.Management/managementGroups")

    #@pytest.mark.custom_mark1
    def test_update_managementgroup_with_displayname_and_parentid(self):
        name = "testcligroupchild"
        displayName = "testcligroupchild"
        parentId = "/providers/Microsoft.Management/managementGroups/testcligroup"
        parentName = "testcligroup"
        self.cmd('account management-group create --name ' + parentName)
        self.cmd('account management-group create --name ' + name)
        managementgroup_update = self.cmd(
            'account management-group update --name ' +
            name +
            ' --display-name ' +
            displayName +
            ' --parent ' +
            parentName).get_output_in_json()
        self.cmd('account management-group delete --name ' + name)
        self.cmd('account management-group delete --name ' + parentName)

        self.assertIsNotNone(managementgroup_update)
        self.assertIsNotNone(managementgroup_update["details"])
        self.assertEqual(
            managementgroup_update["id"],
            "/providers/Microsoft.Management/managementGroups/" + name)
        self.assertEqual(managementgroup_update["name"], name)
        self.assertEqual(managementgroup_update["displayName"], displayName)
        self.assertEqual(
            managementgroup_update["details"]["parent"]["displayName"],
            parentName)
        self.assertEqual(
            managementgroup_update["details"]["parent"]["id"],
            parentId)
        self.assertEqual(
            managementgroup_update["details"]["parent"]["name"],
            parentName)
        self.assertIsNotNone(managementgroup_update["tenantId"])
        self.assertEqual(
            managementgroup_update["type"],
            "Microsoft.Management/managementGroups")

    #@pytest.mark.custom_mark1
    def test_create_delete_group_managementgroup(self):
        self.cmd('account management-group create --name testcligroup')
        self.cmd('account management-group delete --name testcligroup')
