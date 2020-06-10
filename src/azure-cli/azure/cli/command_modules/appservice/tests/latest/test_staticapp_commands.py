# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import mock

from azure.cli.command_modules.appservice.static_sites import *
from azure.mgmt.web.models import StaticSiteARMResource


def _contruct_static_site_object(rg, app_name, location):
    app = StaticSiteARMResource(location=location)
    app.name = app_name
    app.id = \
        "/subscriptions/sub/resourceGroups/{}/providers/Microsoft.Web/staticSites/{}".format(rg, app_name)
    return app


class TestStaticAppCommands(unittest.TestCase):
    def setUp(self):
        self.mock_logger = mock.MagicMock()
        self.mock_cmd = mock.MagicMock()
        self.mock_cmd.cli_ctx = mock.MagicMock()
        self.staticapp_client = mock.MagicMock()

        patcher = mock.patch('azure.cli.command_modules.appservice.static_sites._get_staticsites_client_factory',
                             autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_static_site_client_factory = patcher.start()
        self.mock_static_site_client_factory.return_value = self.staticapp_client

        self.rg1 = 'rg1'
        self.name1 = 'name1'
        self.location1 = 'location1'
        self.app1 = _contruct_static_site_object(self.rg1, self.name1, self.location1)

        self.rg2 = 'rg2'
        self.name2 = 'name2'
        self.location2 = 'location2'
        self.app2 = _contruct_static_site_object(self.rg2, self.name2, self.location2)

        from azure.mgmt.web import WebSiteManagementClient
        from azure.cli.core.adal_authentication import AdalAuthentication
        self.client = WebSiteManagementClient(AdalAuthentication(lambda: ('bearer', 'secretToken')), '123455678')


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
        self.app1 = StaticSiteARMResource(location='westus2')
        self.app2 = StaticSiteARMResource(location='eastus')
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        response = list_staticsites(self.mock_cmd)

        self.assertEqual(len(response), 2)
        self.assertIn(self.app1, response)
        self.assertIn(self.app2, response)


    def test_show_staticapp_with_resourcegroup(self):
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        response = show_staticsite(self.mock_cmd, self.name1, self.rg1)

        self.staticapp_client.get_static_site.assert_called_with(self.rg1, self.name1)
        self.assertEqual(self.app1, response)


    def test_show_staticapp_without_resourcegroup(self):
        self.staticapp_client.get_static_site.return_value = self.app1
        self.staticapp_client.list.return_value = [self.app1, self.app2]

        response = show_staticsite(self.mock_cmd, self.name1)

        self.staticapp_client.get_static_site.assert_called_with(self.rg1, self.name1)
        self.assertEqual(self.app1, response)