# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only, live_only
import pytest

class AzureManagementGroupsScenarioTest(ScenarioTest):
    
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

    def test_create_delete_group_managementgroup(self):
        self.cmd('account management-group create --name testcligroup')
        self.cmd('account management-group delete --name testcligroup')

    @live_only()
    def test_managementgroup_add_remove_subscription(self):
        name = "testcligroup"
        sub = "5602fbd9-fb0d-4fbb-98b3-10c8ea20b6de"
        self.cmd('account management-group create --name ' + name)
        self.cmd('account management-group subscription add --name ' + name 
                 + ' --subscription ' + sub)
        self.cmd('account management-group subscription remove --name ' + name 
                 + ' --subscription ' + sub)
        self.cmd('account management-group delete --name ' + name)

    @live_only()
    def test_managementgroup_show_subscription(self):
        name = "testcligroup"
        subName = "5602fbd9-fb0d-4fbb-98b3-10c8ea20b6de"
        subDisplayName = "Visual Studio Enterprise Subscription"
        subParentId = "/providers/Microsoft.Management/managementGroups/" + name
        self.cmd('account management-group create --name ' + name)
        self.cmd('account management-group subscription add --name ' + name 
                 + ' --subscription ' + subName)
        show_sub = self.cmd('account management-group subscription show --name ' + name 
                 + ' --subscription ' + subName).get_output_in_json()
        self.cmd('account management-group subscription remove --name ' + name 
                 + ' --subscription ' + subName)
        self.cmd('account management-group delete --name ' + name)
        self.assertIsNotNone(show_sub)
        self.assertEqual(show_sub["displayName"], 
                         subDisplayName)
        self.assertEqual(show_sub["id"], 
                         subParentId + "/subscriptions/" + subName)
        self.assertEqual(show_sub["name"], 
                         subName)
        self.assertEqual(show_sub["parent"]["id"], 
                         subParentId)
        self.assertEqual(show_sub["type"], 
                         "Microsoft.Management/managementGroups/subscriptions")

    @live_only()
    def test_managementgroup_show_subscription_under_mg(self):
        name = "testcligroup"
        subName = "5602fbd9-fb0d-4fbb-98b3-10c8ea20b6de"
        subDisplayName = "Visual Studio Enterprise Subscription"
        subParentId = "/providers/Microsoft.Management/managementGroups/" + name
        self.cmd('account management-group create --name ' + name)
        self.cmd('account management-group subscription add --name ' + name 
                 + ' --subscription ' + subName)
        show_sub_under_mg = self.cmd('account management-group subscription show-sub-under-mg --name ' + name).get_output_in_json()
        self.cmd('account management-group subscription remove --name ' + name 
                 + ' --subscription ' + subName)
        self.cmd('account management-group delete --name ' + name)
        self.assertIsNotNone(show_sub_under_mg)
        self.assertEqual(show_sub_under_mg[0]["displayName"], 
                         subDisplayName)
        self.assertEqual(show_sub_under_mg[0]["id"], 
                         subParentId + "/subscriptions/" + subName)
        self.assertEqual(show_sub_under_mg[0]["name"], 
                         subName)
        self.assertEqual(show_sub_under_mg[0]["parent"]["id"], 
                         subParentId)
        self.assertEqual(show_sub_under_mg[0]["type"], 
                         "Microsoft.Management/managementGroups/subscriptions")

    def test_managementgroup_get_entities(self):
        name = "testcligroup"
        self.cmd('account management-group create --name ' + name)
        getEntities = self.cmd('account management-group entities list')
        self.cmd('account management-group delete --name ' + name)
        self.assertIsNotNone(getEntities)

    @live_only()
    def test_managementgroup_hierarchysetting_create_delete(self):
        name = "c7a87cda-9a66-4920-b0f8-869baa04efe0"
        self.cmd('account management-group hierarchy-settings create -n ' + 
                 name + ' -r True')
        self.cmd('account management-group hierarchy-settings delete --yes -n ' + 
                 name)

    @live_only()
    def test_managementgroup_hierarchysetting_create_default_mg(self):
        name = "c7a87cda-9a66-4920-b0f8-869baa04efe0"
        defaultmgName = "defaultmg"
        mgPath = "/providers/Microsoft.Management/managementGroups/"
        self.cmd('account management-group create --name ' + defaultmgName)
        self.cmd('account management-group hierarchy-settings create -n ' + 
                 name + ' -m ' + mgPath + defaultmgName)
        showSetting = self.cmd('account management-group hierarchy-settings list -n' + name).get_output_in_json()
        self.cmd('account management-group hierarchy-settings delete --yes -n ' + 
                 name)
        self.cmd('account management-group delete --name ' + defaultmgName)
        self.assertIsNotNone(showSetting)
        self.assertEqual(showSetting["value"][0]["defaultManagementGroup"], 
                         defaultmgName)
        self.assertEqual(showSetting["value"][0]["id"], 
                         mgPath + name + "/settings/default")
        self.assertEqual(showSetting["value"][0]["name"],
                        "default")
        self.assertEqual(showSetting["value"][0]["type"], 
                         "Microsoft.Management/managementGroups/settings")

    @live_only()
    def test_managementgroup_hierarchysetting_create_auth(self):
        name = "c7a87cda-9a66-4920-b0f8-869baa04efe0"
        mgPath = "/providers/Microsoft.Management/managementGroups/"
        self.cmd('account management-group hierarchy-settings create -n ' + 
                 name + ' -r True')
        showSetting = self.cmd('account management-group hierarchy-settings list -n' + name).get_output_in_json()
        self.cmd('account management-group hierarchy-settings delete --yes -n ' + 
                 name)
        self.assertIsNotNone(showSetting)
        self.assertEqual(showSetting["value"][0]["id"], 
                         mgPath + name + "/settings/default")
        self.assertEqual(showSetting["value"][0]["name"],
                        "default")
        self.assertEqual(showSetting["value"][0]["requireAuthorizationForGroupCreation"],
                        True)
        self.assertEqual(showSetting["value"][0]["type"], 
                         "Microsoft.Management/managementGroups/settings")

    @live_only()
    def test_managementgroup_hierarchysetting_create_default_mg_auth(self):
        name = "c7a87cda-9a66-4920-b0f8-869baa04efe0"
        defaultmgName = "defaultmg"
        mgPath = "/providers/Microsoft.Management/managementGroups/"
        self.cmd('account management-group create --name ' + defaultmgName)
        self.cmd('account management-group hierarchy-settings create -n ' + 
                 name + ' -m ' + mgPath + defaultmgName + 
                 ' -r True')
        showSetting = self.cmd('account management-group hierarchy-settings list -n' + name).get_output_in_json()
        self.cmd('account management-group hierarchy-settings  --yes -n ' + 
                 name)
        self.cmd('account management-group delete --name ' + defaultmgName)
        self.assertEqual(showSetting["value"][0]["defaultManagementGroup"], 
                         defaultmgName)
        self.assertEqual(showSetting["value"][0]["id"], 
                         mgPath + name + "/settings/default")
        self.assertEqual(showSetting["value"][0]["name"],
                        "default")
        self.assertEqual(showSetting["value"][0]["requireAuthorizationForGroupCreation"],
                        True)
        self.assertEqual(showSetting["value"][0]["type"], 
                         "Microsoft.Management/managementGroups/settings")

    @live_only()
    def test_managementgroup_hierarchysetting_update_default_mg(self):
        name = "c7a87cda-9a66-4920-b0f8-869baa04efe0"
        defaultmgName1 = "defaultmg1"
        defaultmgName2 = "defaultmg2"
        mgPath = "/providers/Microsoft.Management/managementGroups/"
        self.cmd('account management-group create --name ' + defaultmgName1)
        self.cmd('account management-group create --name ' + defaultmgName2)
        self.cmd('account management-group hierarchy-settings create -n ' + 
                 name + ' -m ' + mgPath + defaultmgName1)
        self.cmd('account management-group hierarchy-settings update -n ' + 
                 name + ' -m ' + mgPath + defaultmgName2)
        showSetting = self.cmd('account management-group hierarchy-settings list -n' + name).get_output_in_json()
        self.cmd('account management-group hierarchy-settings delete --yes -n ' + 
                 name)
        self.cmd('account management-group delete --name ' + defaultmgName1)
        self.cmd('account management-group delete --name ' + defaultmgName2)
        self.assertIsNotNone(showSetting)
        self.assertEqual(showSetting["value"][0]["defaultManagementGroup"], 
                         defaultmgName2)
        self.assertEqual(showSetting["value"][0]["id"], 
                         mgPath + name + "/settings/default")
        self.assertEqual(showSetting["value"][0]["name"],
                        "default")
        self.assertEqual(showSetting["value"][0]["type"], 
                         "Microsoft.Management/managementGroups/settings")

    @live_only()
    def test_managementgroup_hierarchysetting_create_auth(self):
        name = "c7a87cda-9a66-4920-b0f8-869baa04efe0"
        mgPath = "/providers/Microsoft.Management/managementGroups/"
        self.cmd('account management-group hierarchy-settings create -n ' + 
                 name + ' -r False')
        self.cmd('account management-group hierarchy-settings update -n ' + 
                 name + ' -r True')
        showSetting = self.cmd('account management-group hierarchy-settings list -n' + name).get_output_in_json()
        self.cmd('account management-group hierarchy-settings delete --yes -n ' + 
                 name)
        self.assertIsNotNone(showSetting)
        self.assertEqual(showSetting["value"][0]["id"], 
                         mgPath + name + "/settings/default")
        self.assertEqual(showSetting["value"][0]["name"],
                        "default")
        self.assertEqual(showSetting["value"][0]["requireAuthorizationForGroupCreation"],
                        True)
        self.assertEqual(showSetting["value"][0]["type"], 
                         "Microsoft.Management/managementGroups/settings")

    @live_only()
    def test_managementgroup_hierarchysetting_create_default_mg_auth(self):
        name = "c7a87cda-9a66-4920-b0f8-869baa04efe0"
        defaultmgName1 = "defaultmg1"
        defaultmgName2 = "defaultmg2"
        mgPath = "/providers/Microsoft.Management/managementGroups/"
        self.cmd('account management-group create --name ' + defaultmgName1)
        self.cmd('account management-group create --name ' + defaultmgName2)
        self.cmd('account management-group hierarchy-settings create -n ' + 
                 name + ' -m ' + mgPath + defaultmgName1 + 
                 ' -r False')
        self.cmd('account management-group hierarchy-settings update -n ' + 
                 name + ' -m ' + mgPath + defaultmgName2 +
                 ' -r True')
        showSetting = self.cmd('account management-group hierarchy-settings list -n' + name).get_output_in_json()
        self.cmd('account management-group hierarchy-settings delete --yes -n ' + 
                 name)
        self.cmd('account management-group delete --name ' + defaultmgName1)
        self.cmd('account management-group delete --name ' + defaultmgName2)
        self.assertIsNotNone(showSetting)
        self.assertEqual(showSetting["value"][0]["defaultManagementGroup"], 
                         defaultmgName2)
        self.assertEqual(showSetting["value"][0]["id"], 
                         mgPath + name + "/settings/default")
        self.assertEqual(showSetting["value"][0]["name"],
                        "default")
        self.assertEqual(showSetting["value"][0]["type"], 
                         "Microsoft.Management/managementGroups/settings")

    def test_managementgroup_get_tenant_backfill_status(self):
        backfillStatus  = self.cmd('account management-group tenant-backfill get').get_output_in_json()
        self.assertIsNotNone(backfillStatus)
        self.assertEqual(backfillStatus["status"],
                         "Completed")

    def test_managementgroup_start_tenant_backfill(self):
        startBackfill  = self.cmd('account management-group tenant-backfill start').get_output_in_json()
        self.assertIsNotNone(startBackfill)
        self.assertEqual(startBackfill["status"],
                         "Completed")

    def test_managementgroup_name_availability(self):
        existingMGName = "testcligroup1"
        nonExistingMGName = "testcligroup2"
        badMGName = "!badName"
        self.cmd('account management-group create --name ' + existingMGName)
        alreadyExists = self.cmd('account management-group check-name-availability --name ' + existingMGName).get_output_in_json()
        badName = self.cmd('account management-group check-name-availability --name ' + badMGName).get_output_in_json()
        goodName = self.cmd('account management-group check-name-availability --name ' + nonExistingMGName).get_output_in_json()
        self.cmd('account management-group delete --name ' + existingMGName)
        self.assertIsNotNone(alreadyExists)
        self.assertEqual(alreadyExists["message"],
                         "The group with the specified name already exists")
        self.assertEqual(alreadyExists["nameAvailable"],
                         False)
        self.assertIsNotNone(badName)
        self.assertIn("invalid characters",
                      badName["message"])
        self.assertEqual(badName["nameAvailable"],
                         False)
        self.assertEqual(goodName["nameAvailable"],
                         True)
