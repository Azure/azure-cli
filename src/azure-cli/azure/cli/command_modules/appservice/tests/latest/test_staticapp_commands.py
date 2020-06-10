# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock

from azure.cli.command_modules.appservice.static_sites import *
from azure.mgmt.web.models import StaticSiteARMResource


class TestStaticAppCommands(unittest.TestCase):
    def setUp(self):
        _set_up_client_mock(self)
        _set_up_fake_apps(self)


    def test_list_empty_staticapp(self):
        self.staticapp_client.list.return_value = []

        response = list_staticsites(self.mock_cmd)

        self.assertEqual(len(response), 0)


    def test_list_staticapp_with_resourcegroup(self):
        self.staticapp_client.get_static_sites_by_resource_group.return_value = [self.app1]

        response = list_staticsites(self.mock_cmd, self.rg1)

        self.staticapp_client.get_static_sites_by_resource_group.assert_called_with(self.rg1)
        self.assertEqual(len(response), 1)
        self.assertIn(self.app1, response)


    def test_list_staticapp_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        response = list_staticsites(self.mock_cmd)

        self.assertEqual(len(response), 2)
        self.assertIn(self.app1, response)
        self.assertIn(self.app2, response)


    def test_show_staticapp_with_resourcegroup(self):
        self.staticapp_client.get_static_site.return_value = self.app1

        response = show_staticsite(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.get_static_site.assert_called_with(self.rg1, self.name1)
        self.assertEqual(self.app1, response)


    def test_show_staticapp_with_not_exist_resourcegroup(self):
        self.staticapp_client.get_static_site.side_effect = KeyError('resource group')

        with self.assertRaises(KeyError):
            show_staticsite(self.mock_cmd, self.name1, self.rg1_not_exist)

        self.staticapp_client.get_static_site.assert_called_with(self.rg1_not_exist, self.name1)


    def test_show_staticapp_without_resourcegroup(self):
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        response = show_staticsite(self.mock_cmd, self.name1)

        self.staticapp_client.get_static_site.assert_called_with(self.rg1, self.name1)
        self.assertEqual(self.app1, response)


    #TODO implement this
    def test_show_staticapp_not_exist(self):
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        response = show_staticsite(self.mock_cmd, self.name1)

        self.staticapp_client.get_static_site.assert_called_with(self.rg1, self.name1)
        self.assertEqual(self.app1, response)


    def test_delete_staticapp_with_resourcegroup(self):
        delete_staticsite(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.delete_static_site.assert_called_with(resource_group_name=self.rg1, name=self.name1)


    def test_delete_staticapp_without_resourcegroup(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        delete_staticsite(self.mock_cmd, self.name1)

        self.staticapp_client.delete_static_site.assert_called_with(resource_group_name=self.rg1, name=self.name1)


    #TODO implement this
    def test_delete_staticapp_not_exist(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        delete_staticsite(self.mock_cmd, self.name1)

        self.staticapp_client.delete_static_site.assert_called_with(resource_group_name=self.rg1, name=self.name1)


    #TODO implement this
    def test_create_staticapp(self):
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        response = create_staticsites(
            self.mock_cmd, self.rg1, self.name1, self.location1,
            self.source1, self.branch1, self.token1)

        self.staticapp_client.create_or_update_static_site.assert_called_once()
        self.assertEqual(type(response), StaticSiteARMResource)
        self.assertEqual(response.name, self.name1)
        self.assertEqual(response.resourceGroup, self.rg1)
        self.assertEqual(response.location, self.location1)
        self.assertEqual(response.repositoryUrl, self.source1)
        self.assertEqual(response.branch, self.branch1)
        self.assertEqual(response.sku.tier, 'Free')


def _contruct_static_site_object(rg, app_name, location, source, branch):
    app = StaticSiteARMResource(location=location, repository_url=source, branch=branch)
    app.name = app_name
    app.id = \
        "/subscriptions/sub/resourceGroups/{}/providers/Microsoft.Web/staticSites/{}".format(rg, app_name)
    return app


def _set_up_client_mock(self):
    self.mock_logger = mock.MagicMock()
    self.mock_cmd = mock.MagicMock()
    self.mock_cmd.cli_ctx = mock.MagicMock()
    self.staticapp_client = mock.MagicMock()

    patcher = mock.patch('azure.cli.command_modules.appservice.static_sites._get_staticsites_client_factory',
                         autospec=True)
    self.addCleanup(patcher.stop)
    self.mock_static_site_client_factory = patcher.start()
    self.mock_static_site_client_factory.return_value = self.staticapp_client


def _set_up_fake_apps(self):
    self.rg1 = 'rg1'
    self.rg1_not_exist = 'rg1_not_exist'
    self.name1 = 'name1'
    self.location1 = 'location1'
    self.source1 = 'https://github.com/Contoso/My-First-Static-App'
    self.branch1 = 'dev'
    self.token1 = 'TOKEN_1'
    self.app1 = _contruct_static_site_object(
        self.rg1, self.name1, self.location1,
        self.source1, self.branch1)

    self.rg2 = 'rg2'
    self.name2 = 'name2'
    self.location2 = 'location2'
    self.source2 = 'https://github.com/Contoso/My-Second-Static-App'
    self.branch2 = 'master'
    self.token2 = 'TOKEN_2'
    self.app2 = _contruct_static_site_object(
        self.rg2, self.name2, self.location2,
        self.source2, self.branch2)